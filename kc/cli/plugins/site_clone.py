import os

from cement.core.controller import CementBaseController, expose
from kc.cli.plugins.site_functions import (
    detSitePar, check_domain_exists, site_package_check,
    pre_run_checks, setupdomain, SiteError,
    doCleanupAction, setupdatabase, setupwordpress, setwebrootpermissions,
    display_cache_settings, copyWildcardCert)
from kc.cli.plugins.sitedb import (addNewSite, deleteSiteInfo,
                                   updateSiteInfo)
from kc.core.acme import KCAcme
from kc.core.domainvalidate import KCDomain
from kc.core.git import KCGit
from kc.core.logging import Log
from kc.core.nginxhashbucket import hashbucket
from kc.core.services import KCService
from kc.core.sslutils import SSL
from kc.core.variables import KCVar


class KCSiteCloneController(CementBaseController):
    class Meta:
        label = 'clone'
        stacked_on = 'site'
        stacked_type = 'nested'
        description = ('this commands allow you to clone a site')
        arguments = [
            (['site_name'],
                dict(help='domain name for the site to be cloned.',
                     nargs='?')),
            (['newsite_name'],
                dict(help='domain name for the site to be created.',
                     nargs='?')),
            (['--html'],
                dict(help="create html site", action='store_true')),
            (['--php'],
             dict(help="create php 7.2 site", action='store_true')),
            (['--php72'],
                dict(help="create php 7.2 site", action='store_true')),
            (['--php73'],
                dict(help="create php 7.3 site", action='store_true')),
            (['--php74'],
                dict(help="create php 7.4 site", action='store_true')),
            (['--mysql'],
                dict(help="create mysql site", action='store_true')),
            (['--wp'],
                dict(help="create WordPress single site",
                     action='store_true')),
            (['--wpsubdir'],
                dict(help="create WordPress multisite with subdirectory setup",
                     action='store_true')),
            (['--wpsubdomain'],
                dict(help="create WordPress multisite with subdomain setup",
                     action='store_true')),
            (['--wpfc'],
                dict(help="create WordPress single/multi site with "
                     "Nginx fastcgi_cache",
                     action='store_true')),
            (['--wpsc'],
                dict(help="create WordPress single/multi site with wpsc cache",
                     action='store_true')),
            (['--wprocket'],
             dict(help="create WordPress single/multi site with WP-Rocket",
                  action='store_true')),
            (['--wpce'],
             dict(help="create WordPress single/multi site with Cache-Enabler",
                  action='store_true')),
            (['--wpredis'],
                dict(help="create WordPress single/multi site "
                     "with redis cache",
                     action='store_true')),
            (['-le', '--letsencrypt'],
                dict(help="configure letsencrypt ssl for the site",
                     action='store' or 'store_const',
                     choices=('on', 'subdomain', 'wildcard'),
                     const='on', nargs='?')),
            (['--force'],
                dict(help="force Let's Encrypt certificate issuance",
                     action='store_true')),
            (['--dns'],
                dict(help="choose dns provider api for letsencrypt",
                     action='store' or 'store_const',
                     const='dns_cf', nargs='?')),
            (['--dnsalias'],
                dict(help="set domain used for acme dns alias validation",
                     action='store', nargs='?')),
            (['--hsts'],
                dict(help="enable HSTS for site secured with letsencrypt",
                     action='store_true')),
            (['--ngxblocker'],
                dict(help="enable HSTS for site secured with letsencrypt",
                     action='store_true')),
            (['--user'],
                dict(help="provide user for WordPress site")),
            (['--email'],
                dict(help="provide email address for WordPress site")),
            (['--pass'],
                dict(help="provide password for WordPress user",
                     dest='wppass')),
            (['--proxy'],
                dict(help="create proxy for site", nargs='+')),
            (['--vhostonly'], dict(help="only create vhost and database "
                                   "without installing WordPress",
                                   action='store_true')),
        ]

    @expose(hide=True)
    def default(self):
        pargs = self.app.pargs
        # self.app.render((data), 'default.mustache')
        # Check domain name validation
        data = dict()
        host, port = None, None
        try:
            stype, cache = detSitePar(vars(pargs))
        except RuntimeError as e:
            Log.debug(self, str(e))
            Log.error(self, "Please provide valid options to creating site")

        if stype is None and pargs.proxy:
            stype, cache = 'proxy', ''
            proxyinfo = pargs.proxy[0].strip()
            if not proxyinfo:
                Log.error(self, "Please provide proxy server host information")
            proxyinfo = proxyinfo.split(':')
            host = proxyinfo[0].strip()
            port = '80' if len(proxyinfo) < 2 else proxyinfo[1].strip()
        elif stype is None and not pargs.proxy:
            stype, cache = 'html', 'basic'
        elif stype and pargs.proxy:
            Log.error(self, "proxy should not be used with other site types")

        if not pargs.site_name:
            try:
                while not pargs.site_name:
                    # preprocessing before finalize site name
                    pargs.site_name = (input('Enter site name : ')
                                       .strip())
            except IOError as e:
                Log.debug(self, str(e))
                Log.error(self, "Unable to input site name, Please try again!")

        pargs.site_name = pargs.site_name.strip()
        kc_domain = KCDomain.validate(self, pargs.site_name)
        kc_www_domain = "www.{0}".format(kc_domain)
        (kc_domain_type, kc_root_domain) = KCDomain.getlevel(
            self, kc_domain)
        if not kc_domain.strip():
            Log.error(self, "Invalid domain name, "
                      "Provide valid domain name")

        kc_site_webroot = KCVar.kc_webroot + kc_domain

        if check_domain_exists(self, kc_domain):
            Log.error(self, "site {0} already exists".format(kc_domain))
        elif os.path.isfile('/etc/nginx/sites-available/{0}'
                            .format(kc_domain)):
            Log.error(self, "Nginx configuration /etc/nginx/sites-available/"
                      "{0} already exists".format(kc_domain))

        if stype == 'proxy':
            data = dict(
                site_name=kc_domain, www_domain=kc_www_domain,
                static=True, basic=False, wp=False,
                wpfc=False, wpsc=False, wprocket=False, wpce=False,
                multisite=False, wpsubdir=False, webroot=kc_site_webroot)
            data['proxy'] = True
            data['host'] = host
            data['port'] = port
            data['basic'] = True

        if pargs.php72 or pargs.php73 or pargs.php74:
            data = dict(
                site_name=kc_domain, www_domain=kc_www_domain,
                static=False, basic=False,
                wp=False, wpfc=False, wpsc=False, wprocket=False,
                wpce=False, multisite=False,
                wpsubdir=False, webroot=kc_site_webroot)
            data['basic'] = True

        if stype in ['html', 'php']:
            data = dict(
                site_name=kc_domain, www_domain=kc_www_domain,
                static=True, basic=False, wp=False,
                wpfc=False, wpsc=False, wprocket=False, wpce=False,
                multisite=False, wpsubdir=False, webroot=kc_site_webroot)

            if stype == 'php':
                data['static'] = False
                data['basic'] = True

        elif stype in ['mysql', 'wp', 'wpsubdir', 'wpsubdomain']:

            data = dict(
                site_name=kc_domain, www_domain=kc_www_domain,
                static=False, basic=True, wp=False, wpfc=False,
                wpsc=False, wpredis=False, wprocket=False, wpce=False,
                multisite=False, wpsubdir=False, webroot=kc_site_webroot,
                kc_db_name='', kc_db_user='', kc_db_pass='',
                kc_db_host='')

            if stype in ['wp', 'wpsubdir', 'wpsubdomain']:
                data['wp'] = True
                data['basic'] = False
                data[cache] = True
                data['wp-user'] = pargs.user
                data['wp-email'] = pargs.email
                data['wp-pass'] = pargs.wppass
                if stype in ['wpsubdir', 'wpsubdomain']:
                    data['multisite'] = True
                    if stype == 'wpsubdir':
                        data['wpsubdir'] = True
        else:
            pass

        data['php73'] = False
        data['php74'] = False
        data['php72'] = False

        if data and pargs.php73:
            data['php73'] = True
            data['kc_php'] = 'php73'
        elif data and pargs.php74:
            data['php74'] = True
            data['kc_php'] = 'php74'
        elif data and pargs.php72:
            data['php72'] = True
            data['kc_php'] = 'php72'
        else:
            if self.app.config.has_section('php'):
                config_php_ver = self.app.config.get(
                    'php', 'version')
                if config_php_ver == '7.2':
                    data['php72'] = True
                    data['kc_php'] = 'php72'
                elif config_php_ver == '7.3':
                    data['php73'] = True
                    data['kc_php'] = 'php73'
                elif config_php_ver == '7.4':
                    data['php74'] = True
                    data['kc_php'] = 'php74'
            else:
                data['php73'] = True
                data['kc_php'] = 'php73'

        if ((not pargs.wpfc) and (not pargs.wpsc) and
            (not pargs.wprocket) and
            (not pargs.wpce) and
                (not pargs.wpredis)):
            data['basic'] = True

        if (cache == 'wpredis'):
            cache = 'wpredis'
            data['wpredis'] = True
            data['basic'] = False
            pargs.wpredis = True

        # Check rerequired packages are installed or not
        kc_auth = site_package_check(self, stype)

        try:
            pre_run_checks(self)
        except SiteError as e:
            Log.debug(self, str(e))
            Log.error(self, "NGINX configuration check failed.")

        try:
            try:
                # setup NGINX configuration, and webroot
                setupdomain(self, data)

                # Fix Nginx Hashbucket size error
                hashbucket(self)
            except SiteError as e:
                # call cleanup actions on failure
                Log.info(self, Log.FAIL +
                         "There was a serious error encountered...")
                Log.info(self, Log.FAIL + "Cleaning up afterwards...")
                doCleanupAction(self, domain=kc_domain,
                                webroot=data['webroot'])
                Log.debug(self, str(e))
                Log.error(self, "Check the log for details: "
                          "`tail /var/log/kc/keepcloud.log` "
                          "and please try again")

            if 'proxy' in data.keys() and data['proxy']:
                addNewSite(self, kc_domain, stype, cache, kc_site_webroot)
                # Service Nginx Reload
                if not KCService.reload_service(self, 'nginx'):
                    Log.info(self, Log.FAIL +
                             "There was a serious error encountered...")
                    Log.info(self, Log.FAIL + "Cleaning up afterwards...")
                    doCleanupAction(self, domain=kc_domain)
                    deleteSiteInfo(self, kc_domain)
                    Log.error(self, "service nginx reload failed. "
                              "check issues with `nginx -t` command")
                    Log.error(self, "Check the log for details: "
                              "`tail /var/log/kc/keepcloud.log` "
                              "and please try again")
                if kc_auth and len(kc_auth):
                    for msg in kc_auth:
                        Log.info(self, Log.ENDC + msg, log=False)
                Log.info(self, "Successfully created site"
                         " http://{0}".format(kc_domain))
                return

            if data['php72']:
                php_version = "7.2"
            elif data['php74']:
                php_version = "7.4"
            else:
                php_version = "7.3"

            addNewSite(self, kc_domain, stype, cache, kc_site_webroot,
                       php_version=php_version)

            # Setup database for MySQL site
            if 'kc_db_name' in data.keys() and not data['wp']:
                try:
                    data = setupdatabase(self, data)
                    # Add database information for site into database
                    updateSiteInfo(self, kc_domain, db_name=data['kc_db_name'],
                                   db_user=data['kc_db_user'],
                                   db_password=data['kc_db_pass'],
                                   db_host=data['kc_db_host'])
                except SiteError as e:
                    # call cleanup actions on failure
                    Log.debug(self, str(e))
                    Log.info(self, Log.FAIL +
                             "There was a serious error encountered...")
                    Log.info(self, Log.FAIL + "Cleaning up afterwards...")
                    doCleanupAction(self, domain=kc_domain,
                                    webroot=data['webroot'],
                                    dbname=data['kc_db_name'],
                                    dbuser=data['kc_db_user'],
                                    dbhost=data['kc_db_host'])
                    deleteSiteInfo(self, kc_domain)
                    Log.error(self, "Check the log for details: "
                              "`tail /var/log/kc/keepcloud.log` "
                              "and please try again")

                try:
                    kcdbconfig = open("{0}/wo-config.php"
                                      .format(kc_site_webroot),
                                      encoding='utf-8', mode='w')
                    kcdbconfig.write("<?php \ndefine('DB_NAME', '{0}');"
                                     "\ndefine('DB_USER', '{1}'); "
                                     "\ndefine('DB_PASSWORD', '{2}');"
                                     "\ndefine('DB_HOST', '{3}');\n?>"
                                     .format(data['kc_db_name'],
                                             data['kc_db_user'],
                                             data['wo_db_pass'],
                                             data['kc_db_host']))
                    kcdbconfig.close()
                    stype = 'mysql'
                except IOError as e:
                    Log.debug(self, str(e))
                    Log.debug(self, "Error occured while generating "
                              "kc-config.php")
                    Log.info(self, Log.FAIL +
                             "There was a serious error encountered...")
                    Log.info(self, Log.FAIL + "Cleaning up afterwards...")
                    doCleanupAction(self, domain=kc_domain,
                                    webroot=data['webroot'],
                                    dbname=data['kc_db_name'],
                                    dbuser=data['kc_db_user'],
                                    dbhost=data['kc_db_host'])
                    deleteSiteInfo(self, kc_domain)
                    Log.error(self, "Check the log for details: "
                              "`tail /var/log/kc/keepcloud.log` "
                              "and please try again")

            # Setup WordPress if Wordpress site
            if data['wp']:
                vhostonly = bool(pargs.vhostonly)
                try:
                    kc_wp_creds = setupwordpress(self, data, vhostonly)
                    # Add database information for site into database
                    updateSiteInfo(self, kc_domain,
                                   db_name=data['kc_db_name'],
                                   db_user=data['kc_db_user'],
                                   db_password=data['kc_db_pass'],
                                   db_host=data['kc_db_host'])
                except SiteError as e:
                    # call cleanup actions on failure
                    Log.debug(self, str(e))
                    Log.info(self, Log.FAIL +
                             "There was a serious error encountered...")
                    Log.info(self, Log.FAIL + "Cleaning up afterwards...")
                    doCleanupAction(self, domain=kc_domain,
                                    webroot=data['webroot'],
                                    dbname=data['kc_db_name'],
                                    dbuser=data['kc_db_user'],
                                    dbhost=data['kc_mysql_grant_host'])
                    deleteSiteInfo(self, kc_domain)
                    Log.error(self, "Check the log for details: "
                              "`tail /var/log/kc/keepcloud.log` "
                              "and please try again")

            # Service Nginx Reload call cleanup if failed to reload nginx
            if not KCService.reload_service(self, 'nginx'):
                Log.info(self, Log.FAIL +
                         "There was a serious error encountered...")
                Log.info(self, Log.FAIL + "Cleaning up afterwards...")
                doCleanupAction(self, domain=kc_domain,
                                webroot=data['webroot'])
                if 'kc_db_name' in data.keys():
                    doCleanupAction(self, domain=kc_domain,
                                    dbname=data['kc_db_name'],
                                    dbuser=data['kc_db_user'],
                                    dbhost=data['kc_mysql_grant_host'])
                deleteSiteInfo(self, kc_domain)
                Log.info(self, Log.FAIL + "service nginx reload failed."
                         " check issues with `nginx -t` command.")
                Log.error(self, "Check the log for details: "
                          "`tail /var/log/kc/keepcloud.log` "
                          "and please try again")

            KCGit.add(self, ["/etc/nginx"],
                      msg="{0} created with {1} {2}"
                      .format(kc_www_domain, stype, cache))
            # Setup Permissions for webroot
            try:
                setwebrootpermissions(self, data['webroot'])
            except SiteError as e:
                Log.debug(self, str(e))
                Log.info(self, Log.FAIL +
                         "There was a serious error encountered...")
                Log.info(self, Log.FAIL + "Cleaning up afterwards...")
                doCleanupAction(self, domain=kc_domain,
                                webroot=data['webroot'])
                if 'wo_db_name' in data.keys():
                    print("Inside db cleanup")
                    doCleanupAction(self, domain=kc_domain,
                                    dbname=data['kc_db_name'],
                                    dbuser=data['kc_db_user'],
                                    dbhost=data['kc_mysql_grant_host'])
                deleteSiteInfo(self, kc_domain)
                Log.error(self, "Check the log for details: "
                          "`tail /var/log/kc/keepcloud.log` and "
                          "please try again")

            if kc_auth and len(kc_auth):
                for msg in kc_auth:
                    Log.info(self, Log.ENDC + msg, log=False)

            if data['wp'] and (not pargs.vhostonly):
                Log.info(self, Log.ENDC + "WordPress admin user :"
                         " {0}".format(kc_wp_creds['wp_user']), log=False)
                Log.info(self, Log.ENDC + "WordPress admin password : {0}"
                         .format(kc_wp_creds['wp_pass']), log=False)

                display_cache_settings(self, data)

            Log.info(self, "Successfully created site"
                     " http://{0}".format(kc_domain))
        except SiteError:
            Log.error(self, "Check the log for details: "
                      "`tail /var/log/kc/keepcloud.log` and please try again")

        if pargs.letsencrypt:
            acme_domains = []
            data['letsencrypt'] = True
            letsencrypt = True
            Log.debug(self, "Going to issue Let's Encrypt certificate")
            acmedata = dict(
                acme_domains, dns=False, acme_dns='dns_cf',
                dnsalias=False, acme_alias='', keylength='')
            if self.app.config.has_section('letsencrypt'):
                acmedata['keylength'] = self.app.config.get(
                    'letsencrypt', 'keylength')
            else:
                acmedata['keylength'] = 'ec-384'
            if pargs.dns:
                Log.debug(self, "DNS validation enabled")
                acmedata['dns'] = True
                if not pargs.dns == 'dns_cf':
                    Log.debug(self, "DNS API : {0}".format(pargs.dns))
                    acmedata['acme_dns'] = pargs.dns
            if pargs.dnsalias:
                Log.debug(self, "DNS Alias enabled")
                acmedata['dnsalias'] = True
                acmedata['acme_alias'] = pargs.dnsalias

            # detect subdomain and set subdomain variable
            if pargs.letsencrypt == "subdomain":
                Log.warn(
                    self, 'Flag --letsencrypt=subdomain is '
                    'deprecated and not required anymore.')
                acme_subdomain = True
                acme_wildcard = False
            elif pargs.letsencrypt == "wildcard":
                acme_wildcard = True
                acme_subdomain = False
                acmedata['dns'] = True
            else:
                if ((kc_domain_type == 'subdomain')):
                    Log.debug(self, "Domain type = {0}"
                              .format(kc_domain_type))
                    acme_subdomain = True
                else:
                    acme_subdomain = False
                    acme_wildcard = False

            if acme_subdomain is True:
                Log.info(self, "Certificate type : subdomain")
                acme_domains = acme_domains + ['{0}'.format(kc_domain)]
            elif acme_wildcard is True:
                Log.info(self, "Certificate type : wildcard")
                acme_domains = acme_domains + ['{0}'.format(kc_domain),
                                               '*.{0}'.format(kc_domain)]
            else:
                Log.info(self, "Certificate type : domain")
                acme_domains = acme_domains + ['{0}'.format(kc_domain),
                                               'www.{0}'.format(kc_domain)]

            if KCAcme.cert_check(self, kc_domain):
                SSL.archivedcertificatehandle(self, kc_domain, acme_domains)
            else:
                if acme_subdomain is True:
                    # check if a wildcard cert for the root domain exist
                    Log.debug(self, "checkWildcardExist on *.{0}"
                              .format(kc_root_domain))
                    if SSL.checkwildcardexist(self, kc_root_domain):
                        Log.info(self, "Using existing Wildcard SSL "
                                 "certificate from {0} to secure {1}"
                                 .format(kc_root_domain, kc_domain))
                        Log.debug(self, "symlink wildcard "
                                  "cert between {0} & {1}"
                                  .format(kc_domain, kc_root_domain))
                        # copy the cert from the root domain
                        copyWildcardCert(self, kc_domain, kc_root_domain)
                    else:
                        # check DNS records before issuing cert
                        if not acmedata['dns'] is True:
                            if not pargs.force:
                                if not KCAcme.check_dns(self, acme_domains):
                                    Log.error(self,
                                              "Aborting SSL "
                                              "certificate issuance")
                        Log.debug(self, "Setup Cert with acme.sh for {0}"
                                  .format(kc_domain))
                        if KCAcme.setupletsencrypt(
                                self, acme_domains, acmedata):
                            KCAcme.deploycert(self, kc_domain)
                else:
                    if not acmedata['dns'] is True:
                        if not pargs.force:
                            if not KCAcme.check_dns(self, acme_domains):
                                Log.error(self,
                                          "Aborting SSL certificate issuance")
                    if KCAcme.setupletsencrypt(
                            self, acme_domains, acmedata):
                        KCAcme.deploycert(self, kc_domain)

                if pargs.hsts:
                    SSL.setuphsts(self, kc_domain)

                SSL.httpsredirect(self, kc_domain, acme_domains, True)
                SSL.siteurlhttps(self, kc_domain)
                if not KCService.reload_service(self, 'nginx'):
                    Log.error(self, "service nginx reload failed. "
                              "check issues with `nginx -t` command")
                Log.info(self, "Congratulations! Successfully Configured "
                         "SSL on https://{0}".format(kc_domain))

                # Add nginx conf folder into GIT
                KCGit.add(self, ["{0}/conf/nginx".format(kc_site_webroot)],
                          msg="Adding letsencrypts config of site: {0}"
                          .format(kc_domain))
                updateSiteInfo(self, kc_domain, ssl=letsencrypt)
