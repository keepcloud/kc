""" wo site update """
import json
import os

from cement.core.controller import CementBaseController, expose

from kc.cli.plugins.site_functions import (
    detSitePar, site_package_check,
    pre_run_checks, setupdomain, SiteError,
    setupdatabase, setupwordpress, setwebrootpermissions,
    display_cache_settings, copyWildcardCert,
    updatewpuserpassword, setupngxblocker, setupwp_plugin,
    setupwordpressnetwork, installwp_plugin, sitebackup, uninstallwp_plugin)
from kc.cli.plugins.sitedb import (getAllsites,
                                   getSiteInfo, updateSiteInfo)
from kc.core.acme import KCAcme
from kc.core.domainvalidate import KCDomain
from kc.core.fileutils import KCFileUtils
from kc.core.git import KCGit
from kc.core.logging import Log
from kc.core.services import KCService
from kc.core.sslutils import SSL
from kc.core.variables import KCVar


class KCSiteUpdateController(CementBaseController):
    class Meta:
        label = 'update'
        stacked_on = 'site'
        stacked_type = 'nested'
        description = ('This command updates websites configuration to '
                       'another as per the options are provided')
        arguments = [
            (['site_name'],
                dict(help='domain name for the site to be updated',
                     nargs='?')),
            (['--password'],
                dict(help="update to password for wordpress site user",
                     action='store_true')),
            (['--html'],
                dict(help="update to html site", action='store_true')),
            (['--php'],
             dict(help="update to php site", action='store_true')),
            (['--php72'],
                dict(help="update to php72 site", action='store_true')),
            (['--php73'],
                dict(help="update to php73 site", action='store_true')),
            (['--php74'],
                dict(help="update to php74 site", action='store_true')),
            (['--php80'],
                dict(help="update to php80 site", action='store_true')),
            (['--php81'],
                dict(help="update to php81 site", action='store_true')),
            (['--mysql'],
                dict(help="update to mysql site", action='store_true')),
            (['--wp'],
                dict(help="update to wordpress single site",
                     action='store_true')),
            (['--wpsubdir'],
                dict(help="update to wpsubdir site", action='store_true')),
            (['--wpsubdomain'],
                dict(help="update to  wpsubdomain site", action='store_true')),
            (['--wpfc'],
                dict(help="update to wpfc cache", action='store_true')),
            (['--wpsc'],
                dict(help="update to wpsc cache", action='store_true')),
            (['--wprocket'],
                dict(help="update to WP-Rocket cache", action='store_true')),
            (['--wpce'],
                dict(help="update to Cache-Enabler cache",
                     action='store_true')),
            (['--wpredis'],
                dict(help="update to redis cache", action='store_true')),
            (['-le', '--letsencrypt'],
                dict(help="configure letsencrypt ssl for the site",
                     action='store' or 'store_const',
                     choices=('on', 'off', 'renew', 'subdomain',
                              'wildcard', 'clean', 'purge'),
                     const='on', nargs='?')),
            (['--force'],
                dict(help="force LetsEncrypt certificate issuance/renewal",
                     action='store_true')),
            (['--dns'],
                dict(help="choose dns provider api for letsencrypt",
                     action='store' or 'store_const',
                     const='dns_cf', nargs='?')),
            (['--dnsalias'],
                dict(help="set domain used for acme dns alias validation",
                     action='store', nargs='?')),
            (['--hsts'],
                dict(help="configure hsts for the site",
                     action='store' or 'store_const',
                     choices=('on', 'off'),
                     const='on', nargs='?')),
            (['--ngxblocker'],
                dict(help="enable Ultimate Nginx bad bot blocker",
                     action='store' or 'store_const',
                     choices=('on', 'off'),
                     const='on', nargs='?')),
            (['--proxy'],
                dict(help="update to proxy site", nargs='+')),
            (['--all'],
                dict(help="update all sites", action='store_true')),
        ]

    @expose(help="Update site type or cache")
    def default(self):
        pargs = self.app.pargs

        if pargs.all:
            if pargs.site_name:
                Log.error(self, "`--all` option cannot be used with site name"
                          " provided")
            if pargs.html:
                Log.error(self, "No site can be updated to html")

            if not (pargs.php or pargs.php72 or pargs.php73 or pargs.php74 or
                    pargs.php80 or pargs.php81 or
                    pargs.mysql or pargs.wp or pargs.wpsubdir or
                    pargs.wpsubdomain or pargs.wpfc or pargs.wpsc or
                    pargs.wprocket or pargs.wpce or
                    pargs.wpredis or pargs.letsencrypt or pargs.hsts or
                    pargs.dns or pargs.force):
                Log.error(self, "Please provide options to update sites.")

        if pargs.all:
            if pargs.site_name:
                Log.error(self, "`--all` option cannot be used with site name"
                          " provided")

            sites = getAllsites(self)
            if not sites:
                pass
            else:
                for site in sites:
                    pargs.site_name = site.sitename
                    Log.info(self, Log.ENDC + Log.BOLD + "Updating site {0},"
                             " please wait..."
                             .format(pargs.site_name))
                    self.doupdatesite(pargs)
                    print("\n")
        else:
            self.doupdatesite(pargs)

    def doupdatesite(self, pargs):
        pargs = self.app.pargs
        letsencrypt = False
        php73 = False
        php74 = False
        php72 = False
        php80 = False
        php81 = False

        data = dict()
        try:
            stype, cache = detSitePar(vars(pargs))
        except RuntimeError as e:
            Log.debug(self, str(e))
            Log.error(self, "Please provide valid options combination for"
                      " site update")

        if stype is None and pargs.proxy:
            stype, cache = 'proxy', ''
            proxyinfo = pargs.proxy[0].strip()
            if not proxyinfo:
                Log.error(self, "Please provide proxy server host information")
            proxyinfo = proxyinfo.split(':')
            host = proxyinfo[0].strip()
            port = '80' if len(proxyinfo) < 2 else proxyinfo[1].strip()
        elif stype is None and not (pargs.proxy or pargs.letsencrypt):
            stype, cache = 'html', 'basic'
        elif stype and pargs.proxy:
            Log.error(self, "--proxy can not be used with other site types")

        if not pargs.site_name:
            try:
                while not pargs.site_name:
                    pargs.site_name = (input('Enter site name : ').strip())
            except IOError:
                Log.error(self, 'Unable to input site name, Please try again!')

        pargs.site_name = pargs.site_name.strip()
        kc_domain = KCDomain.validate(self, pargs.site_name)
        kc_www_domain = "www.{0}".format(kc_domain)
        (kc_domain_type, kc_root_domain) = KCDomain.getlevel(
            self, kc_domain)
        kc_site_webroot = KCVar.kc_webroot + kc_domain
        check_site = getSiteInfo(self, kc_domain)

        if check_site is None:
            Log.error(self, " Site {0} does not exist.".format(kc_domain))
        else:
            oldsitetype = check_site.site_type
            oldcachetype = check_site.cache_type
            check_ssl = check_site.is_ssl
            check_php_version = check_site.php_version

            old_php72 = bool(check_php_version == "7.2")
            old_php73 = bool(check_php_version == "7.3")
            old_php74 = bool(check_php_version == "7.4")
            old_php80 = bool(check_php_version == "8.0")
            old_php81 = bool(check_php_version == "8.1")

        if ((pargs.password or pargs.hsts or
             pargs.ngxblocker or pargs.letsencrypt == 'renew') and not (
            pargs.html or pargs.php or pargs.php72 or pargs.php73 or
            pargs.php74 or pargs.php80 or pargs.php81 or
            pargs.mysql or pargs.wp or pargs.wpfc or pargs.wpsc or
            pargs.wprocket or pargs.wpce or
                pargs.wpsubdir or pargs.wpsubdomain)):

            # update wordpress password
            if (pargs.password):
                try:
                    updatewpuserpassword(self, kc_domain, kc_site_webroot)
                except SiteError as e:
                    Log.debug(self, str(e))
                    Log.info(self, "\nPassword Unchanged.")
                return 0

            # setup hsts
            if (pargs.hsts):
                if pargs.hsts == "on":
                    SSL.setuphsts(self, kc_domain, enable=True)
                elif pargs.hsts == "off":
                    SSL.setuphsts(self, kc_domain, enable=False)
                    # Service Nginx Reload
                if not kcService.reload_service(self, 'nginx'):
                    Log.error(
                        self, "service nginx reload failed. "
                        "check issues with `nginx -t` command")

            # setup ngxblocker
            if (pargs.ngxblocker):
                if pargs.ngxblocker == "on":
                    if os.path.isdir('/etc/nginx/bots.d'):
                        try:
                            setupngxblocker(self, kc_domain)
                        except SiteError as e:
                            Log.debug(self, str(e))
                            Log.info(self, "\nngxblocker not enabled.")
                    else:
                        Log.error(self, 'ngxblocker stack is not installed')
                elif pargs.ngxblocker == "off":
                    try:
                        setupngxblocker(self, kc_domain, False)
                    except SiteError as e:
                        Log.debug(self, str(e))
                        Log.info(self, "\nngxblocker not enabled.")

                # Service Nginx Reload
                if not KCService.reload_service(self, 'nginx'):
                    Log.error(self, "service nginx reload failed. "
                              "check issues with `nginx -t` command")

            # letsencryot rebew
            if (pargs.letsencrypt == 'renew'):
                if KCAcme.cert_check(self, kc_domain):
                    if not pargs.force:
                        if (SSL.getexpirationdays(self, kc_domain) > 30):
                            Log.error(
                                self, "Your cert will expire in more "
                                "than 30 days ( " +
                                str(SSL.getexpirationdays(self, kc_domain)) +
                                " days).\nAdd \'--force\' to force to renew")
                    Log.wait(self, "Renewing SSL certificate")
                    if KCAcme.renew(self, kc_domain):
                        Log.valide(self, "Renewing SSL certificate")
                else:
                    Log.error(self, "Certificate doesn't exist")
                return 0

        if (((stype == 'php' and
              oldsitetype not in ['html', 'proxy', 'php', 'php72',
                                  'php73', 'php74', 'php80', 'php81']) or
             (stype == 'mysql' and oldsitetype not in [
                 'html', 'php', 'php72', 'php73', 'php74', 'php80', 'php81',
                 'proxy']) or
             (stype == 'wp' and oldsitetype not in [
                 'html', 'php', 'php72', 'php73', 'php74', 'php80', 'php81',
                 'mysql', 'proxy', 'wp']) or
             (stype == 'wpsubdir' and oldsitetype in ['wpsubdomain']) or
             (stype == 'wpsubdomain' and oldsitetype in ['wpsubdir']) or
             (stype == oldsitetype and cache == oldcachetype)) and
                not (pargs.php72 or pargs.php73 or
                     pargs.php74 or pargs.php80 or
                     pargs.php81)):
            Log.info(self, Log.FAIL + "can not update {0} {1} to {2} {3}".
                     format(oldsitetype, oldcachetype, stype, cache))
            return 1

        if stype == 'proxy':
            data['site_name'] = kc_domain
            data['www_domain'] = kc_www_domain
            data['proxy'] = True
            data['host'] = host
            data['port'] = port
            data['webroot'] = kc_site_webroot
            data['currsitetype'] = oldsitetype
            data['currcachetype'] = oldcachetype

        if stype == 'php':
            data = dict(
                site_name=kc_domain, www_domain=kc_www_domain,
                static=False, basic=True, wp=False, wpfc=False,
                php72=False, php73=False, php74=False,
                php80=False, php81=False,
                wpsc=False, wpredis=False, wprocket=False, wpce=False,
                multisite=False, wpsubdir=False, webroot=kc_site_webroot,
                currsitetype=oldsitetype, currcachetype=oldcachetype)

        elif stype in ['mysql', 'wp', 'wpsubdir', 'wpsubdomain']:
            data = dict(
                site_name=kc_domain, www_domain=kc_www_domain,
                static=False, basic=True, wp=False, wpfc=False,
                wpsc=False, wpredis=False, wprocket=False, wpce=False,
                multisite=False, wpsubdir=False, webroot=kc_site_webroot,
                kc_db_name='', kc_db_user='', kc_db_pass='',
                kc_db_host='',
                currsitetype=oldsitetype, currcachetype=oldcachetype)

        if stype in ['wp', 'wpsubdir', 'wpsubdomain']:
            data['wp'] = True
            data['basic'] = False
            data[cache] = True
            if stype in ['wpsubdir', 'wpsubdomain']:
                data['multisite'] = True
                if stype == 'wpsubdir':
                    data['wpsubdir'] = True

        if ((pargs.php72 or pargs.php73 or
             pargs.php74 or pargs.php80 or pargs.php81) and (not data)):
            Log.debug(
                self, "pargs php72, or php73, or php74, "
                "or php80, or php81 enabled")
            data = dict(
                site_name=kc_domain,
                www_domain=kc_www_domain,
                currsitetype=oldsitetype,
                currcachetype=oldcachetype,
                webroot=kc_site_webroot)
            stype = oldsitetype
            cache = oldcachetype
            if oldsitetype == 'html' or oldsitetype == 'proxy':
                data['static'] = False
                data['wp'] = False
                data['multisite'] = False
                data['wpsubdir'] = False
            elif (oldsitetype == 'php' or oldsitetype == 'mysql' or
                  oldsitetype == 'php73' or oldsitetype == 'php74' or
                  oldsitetype == 'php80' or oldsitetype == 'php81'):
                data['static'] = False
                data['wp'] = False
                data['multisite'] = False
                data['wpsubdir'] = False
            elif oldsitetype == 'wp':
                data['static'] = False
                data['wp'] = True
                data['multisite'] = False
                data['wpsubdir'] = False
            elif oldsitetype == 'wpsubdir':
                data['static'] = False
                data['wp'] = True
                data['multisite'] = True
                data['wpsubdir'] = True
            elif oldsitetype == 'wpsubdomain':
                data['static'] = False
                data['wp'] = True
                data['multisite'] = True
                data['wpsubdir'] = False

            if oldcachetype == 'basic':
                data['basic'] = True
                data['wpfc'] = False
                data['wpsc'] = False
                data['wpredis'] = False
                data['wprocket'] = False
                data['wpce'] = False
            elif oldcachetype == 'wpfc':
                data['basic'] = False
                data['wpfc'] = True
                data['wpsc'] = False
                data['wpredis'] = False
                data['wprocket'] = False
                data['wpce'] = False
            elif oldcachetype == 'wpsc':
                data['basic'] = False
                data['wpfc'] = False
                data['wpsc'] = True
                data['wpredis'] = False
                data['wprocket'] = False
                data['wpce'] = False
            elif oldcachetype == 'wpredis':
                data['basic'] = False
                data['wpfc'] = False
                data['wpsc'] = False
                data['wpredis'] = True
                data['wprocket'] = False
                data['wpce'] = False
            elif oldcachetype == 'wprocket':
                data['basic'] = False
                data['wpfc'] = False
                data['wpsc'] = False
                data['wpredis'] = False
                data['wprocket'] = True
                data['wpce'] = False
            elif oldcachetype == 'wpce':
                data['basic'] = False
                data['wpfc'] = False
                data['wpsc'] = False
                data['wpredis'] = False
                data['wprocket'] = False
                data['wpce'] = True

        if pargs.php72:
            Log.debug(self, "pargs.php72 detected")
            data['php72'] = True
            php72 = True
        elif pargs.php73:
            Log.debug(self, "pargs.php73 detected")
            data['php73'] = True
            php73 = True
        elif pargs.php74:
            Log.debug(self, "pargs.php74 detected")
            data['php74'] = True
            php74 = True
        elif pargs.php80:
            Log.debug(self, "pargs.php80 detected")
            data['php80'] = True
            php80 = True
        elif pargs.php81:
            Log.debug(self, "pargs.php81 detected")
            data['php81'] = True
            php81 = True

        if pargs.php72:
            if php72 is old_php72:
                Log.info(self, "PHP 7.2 is already enabled for given "
                         "site")
                pargs.php72 = False

        if pargs.php73:
            if php73 is old_php73:
                Log.info(self, "PHP 7.3 is already enabled for given "
                         "site")
                pargs.php73 = False

        if pargs.php74:
            if php74 is old_php74:
                Log.info(self, "PHP 7.4 is already enabled for given "
                         "site")
                pargs.php74 = False

        if pargs.php80:
            if php80 is old_php80:
                Log.info(self, "PHP 8.0 is already enabled for given "
                         "site")
                pargs.php80 = False

        if pargs.php81:
            if php81 is old_php81:
                Log.info(self, "PHP 8.1 is already enabled for given "
                         "site")
                pargs.php81 = False

        if (data and (not pargs.php73) and
                (not pargs.php74) and (not pargs.php72) and
                (not pargs.php80) and (not pargs.php81)):
            data['php72'] = bool(old_php72 is True)
            Log.debug(self, "data php72 = {0}".format(data['php72']))
            php72 = bool(old_php72 is True)
            data['php73'] = bool(old_php73 is True)
            Log.debug(self, "data php73 = {0}".format(data['php73']))
            php73 = bool(old_php73 is True)
            data['php74'] = bool(old_php74 is True)
            Log.debug(self, "data php74 = {0}".format(data['php74']))
            php74 = bool(old_php74 is True)
            data['php80'] = bool(old_php80 is True)
            Log.debug(self, "data php80 = {0}".format(data['php80']))
            php80 = bool(old_php80 is True)
            data['php81'] = bool(old_php81 is True)
            Log.debug(self, "data php81 = {0}".format(data['php81']))
            php81 = bool(old_php81 is True)

        if pargs.letsencrypt:
            acme_domains = []
            acmedata = dict(acme_domains, dns=False, acme_dns='dns_cf',
                            dnsalias=False, acme_alias='', keylength='')
            acmedata['keylength'] = self.app.config.get('letsencrypt',
                                                        'keylength')
            if pargs.letsencrypt == 'on':
                data['letsencrypt'] = True
                letsencrypt = True
                acme_subdomain = bool(kc_domain_type == 'subdomain')
                acme_wildcard = False
            elif pargs.letsencrypt == 'subdomain':
                data['letsencrypt'] = True
                letsencrypt = True
                acme_subdomain = True
                acme_wildcard = False
            elif pargs.letsencrypt == 'wildcard':
                data['letsencrypt'] = True
                letsencrypt = True
                acme_wildcard = True
                acme_subdomain = False
                acmedata['dns'] = True
            elif pargs.letsencrypt == 'off':
                data['letsencrypt'] = False
                letsencrypt = False
                acme_subdomain = False
                acme_wildcard = False
            elif pargs.letsencrypt == 'clean':
                data['letsencrypt'] = False
                letsencrypt = False
                acme_subdomain = False
                acme_wildcard = False
            elif pargs.letsencrypt == 'purge':
                data['letsencrypt'] = False
                letsencrypt = False
                acme_subdomain = False
                acme_wildcard = False
            else:
                data['letsencrypt'] = False
                letsencrypt = False
                acme_subdomain = False
                acme_wildcard = False

            if not (acme_subdomain is True):
                if letsencrypt is check_ssl:
                    if letsencrypt is False:
                        Log.error(self, "SSL is not configured for given "
                                  "site")
                    elif letsencrypt is True:
                        Log.error(self, "SSL is already configured for given "
                                  "site")
                    pargs.letsencrypt = False

        if pargs.all and pargs.letsencrypt == "off":
            if letsencrypt is check_ssl:
                if letsencrypt is False:
                    Log.error(self, "HTTPS is not configured for given "
                              "site", False)
                    return 0

        if pargs.wpredis and data['currcachetype'] != 'wpredis':
            data['wpredis'] = True
            data['basic'] = False
            cache = 'wpredis'

        if pargs.wprocket and data['currcachetype'] != 'wprocket':
            data['wprocket'] = True
            data['basic'] = False
            cache = 'wprocket'

        if pargs.wpce and data['currcachetype'] != 'wpce':
            data['wpce'] = True
            data['basic'] = False
            cache = 'wpce'

        if ((php73 is old_php73) and (php72 is old_php72) and
            (php74 is old_php74) and (php80 is old_php80) and
            (php81 is old_php81) and
            (stype == oldsitetype and
             cache == oldcachetype)):
            Log.debug(self, "Nothing to update")
            return 1

        if php73 is True:
            data['kc_php'] = 'php73'
            check_php_version = '7.3'
        elif php74 is True:
            data['kc_php'] = 'php74'
            check_php_version = '7.4'
        elif php72 is True:
            data['kc_php'] = 'php72'
            check_php_version = '7.2'
        elif php80 is True:
            data['kc_php'] = 'php80'
            check_php_version = '8.0'
        elif php81 is True:
            data['kc_php'] = 'php81'
            check_php_version = '8.1'
        else:
            data['kc_php'] = 'php80'
            check_php_version = '8.0'

        if pargs.hsts:
            data['hsts'] = bool(pargs.hsts == "on")

        if pargs.ngxblocker:
            ngxblocker = bool(pargs.ngxblocker == 'on')

        if not data:
            Log.error(self, "Cannot update {0}, Invalid Options"
                      .format(kc_domain))

        kc_auth = site_package_check(self, stype)
        data['kc_db_name'] = check_site.db_name
        data['kc_db_user'] = check_site.db_user
        data['kc_db_pass'] = check_site.db_password
        data['kc_db_host'] = check_site.db_host

        if not (pargs.letsencrypt or pargs.hsts or pargs.ngxblocker):
            try:
                pre_run_checks(self)
            except SiteError as e:
                Log.debug(self, str(e))
                Log.error(self, "NGINX configuration check failed.")

            try:
                sitebackup(self, data)
            except Exception as e:
                Log.debug(self, str(e))
                Log.info(self, Log.FAIL + "Check the log for details: "
                         "`tail /var/log/kc/keepcloud.log` and please try again")
                return 1

            # setup NGINX configuration, and webroot
            try:
                setupdomain(self, data)
            except SiteError as e:
                Log.debug(self, str(e))
                Log.info(self, Log.FAIL + "Update site failed."
                         "Check the log for details:"
                         "`tail /var/log/kc/keepcloud.log` and please try again")
                return 1

        if 'proxy' in data.keys() and data['proxy']:
            updateSiteInfo(self, kc_domain, stype=stype, cache=cache,
                           ssl=(bool(check_site.is_ssl)))
            Log.info(self, "Successfully updated site"
                     " http://{0}".format(kc_domain))
            return 0

        if pargs.letsencrypt:
            if data['letsencrypt'] is True:
                # DNS API configuration
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
                # Set list of domains to secure
                if acme_subdomain is True:
                    Log.info(self, "Certificate type : subdomain")
                    acme_domains = acme_domains + [
                        '{0}'.format(kc_domain)]
                elif acme_wildcard is True:
                    Log.info(self, "Certificate type : wildcard")
                    acme_domains = acme_domains + [
                        '{0}'.format(kc_domain),
                        '*.{0}'.format(kc_domain)]
                else:
                    Log.info(self, "Certificate type : domain")
                    acme_domains = acme_domains + [
                        '{0}'.format(kc_domain),
                        'www.{0}'.format(kc_domain)]

                if KCAcme.cert_check(self, kc_domain):
                    if SSL.archivedcertificatehandle(
                            self, kc_domain, acme_domains):
                        letsencrypt = True
                else:
                    if acme_subdomain:
                        Log.debug(self, "checkWildcardExist on *.{0}"
                                  .format(kc_root_domain))
                        if SSL.checkwildcardexist(self, kc_root_domain):
                            Log.info(
                                self, "Using existing Wildcard SSL "
                                "certificate from {0} to secure {1}"
                                .format(kc_root_domain, kc_domain))
                            Log.debug(
                                self, "symlink wildcard "
                                "cert between {0} & {1}"
                                .format(kc_domain, kc_root_domain))
                            # copy the cert from the root domain
                            copyWildcardCert(self, kc_domain,
                                             kc_root_domain)
                        else:
                            # check DNS records before issuing cert
                            if not acmedata['dns'] is True:
                                if not pargs.force:
                                    if not KCAcme.check_dns(self,
                                                            acme_domains):
                                        Log.error(
                                            self,
                                            "Aborting SSL certificate "
                                            "issuance")
                            Log.debug(
                                self, "Setup Cert with acme.sh for {0}"
                                .format(kc_domain))
                            if KCAcme.setupletsencrypt(
                                    self, acme_domains, acmedata):
                                KCAcme.deploycert(self, kc_domain)
                            else:
                                Log.error(
                                    self, "Unable to issue certificate")
                    else:
                        # check DNS records before issuing cert
                        if not acmedata['dns'] is True:
                            if not pargs.force:
                                if not KCAcme.check_dns(self,
                                                        acme_domains):
                                    Log.error(
                                        self,
                                        "Aborting SSL "
                                        "certificate issuance")
                        if KCAcme.setupletsencrypt(
                                self, acme_domains, acmedata):
                            KCAcme.deploycert(self, kc_domain)
                        else:
                            Log.error(self, "Unable to issue certificate")

                    SSL.httpsredirect(
                        self, kc_domain, acme_domains, redirect=True)
                    SSL.siteurlhttps(self, kc_domain)

                if not KCService.reload_service(self, 'nginx'):
                    Log.error(self, "service nginx reload failed. "
                              "check issues with `nginx -t` command")
                Log.info(self, "Congratulations! Successfully "
                         "Configured SSL on https://{0}".format(kc_domain))
                letsencrypt = True
                if (SSL.getexpirationdays(self, kc_domain) > 0):
                    Log.info(self, "Your cert will expire within " +
                             str(SSL.getexpirationdays(self, kc_domain)) +
                             " days.")
                else:
                    Log.warn(
                        self, "Your cert already EXPIRED ! "
                        ".PLEASE renew soon . ")

            elif data['letsencrypt'] is False:
                if pargs.letsencrypt == "off":
                    if os.path.islink("{0}/conf/nginx/ssl.conf"
                                      .format(kc_site_webroot)):
                        KCFileUtils.remove_symlink(self,
                                                   "{0}/conf/nginx/ssl.conf"
                                                   .format(kc_site_webroot))
                    elif os.path.isfile("{0}/conf/nginx/ssl.conf"
                                        .format(kc_site_webroot)):
                        Log.info(self, 'Setting Nginx configuration')
                        KCFileUtils.mvfile(self, "{0}/conf/nginx/ssl.conf"
                                           .format(kc_site_webroot),
                                           '{0}/conf/nginx/ssl.conf.disabled'
                                           .format(kc_site_webroot))
                        SSL.httpsredirect(
                            self, kc_domain, acmedata, redirect=False)
                        if os.path.isfile("{0}/conf/nginx/hsts.conf"
                                          .format(kc_site_webroot)):
                            KCFileUtils.mvfile(self, "{0}/conf/nginx/hsts.conf"
                                               .format(kc_site_webroot),
                                               '{0}/conf/nginx/'
                                               'hsts.conf.disabled'
                                               .format(kc_site_webroot))
                        # find all broken symlinks
                        sympath = "/var/www"
                        KCFileUtils.findBrokenSymlink(self, sympath)

                elif (pargs.letsencrypt == "clean" or
                      pargs.letsencrypt == "purge"):
                    KCAcme.removeconf(self, kc_domain)
                    # find all broken symlinks
                    sympath = "/var/www"
                    KCFileUtils.findBrokenSymlink(self, sympath)
                if not KCService.reload_service(self, 'nginx'):
                    Log.error(self, "service nginx reload failed. "
                              "check issues with `nginx -t` command")
                    # Log.info(self,"Removing Cron Job set for cert
                    # auto-renewal") KCCron.remove_cron(self,'kc site
                    # update {0} --le=renew --min_expiry_limit 30
                    # 2> \/dev\/null'.format(kc_domain))
                Log.info(self, "Successfully Disabled SSl for Site "
                         " http://{0}".format(kc_domain))
                letsencrypt = False

            # Add nginx conf folder into GIT
            KCGit.add(self, ["{0}/conf/nginx".format(kc_site_webroot)],
                      msg="Adding letsencrypts config of site: {0}"
                      .format(kc_domain))
            updateSiteInfo(self, kc_domain, ssl=letsencrypt)
            return 0

        if pargs.hsts:
            if data['hsts'] is True:
                if os.path.isfile(("{0}/conf/nginx/ssl.conf")
                                  .format(kc_site_webroot)):
                    if not os.path.isfile("{0}/conf/nginx/hsts.conf"
                                          .format(kc_site_webroot)):
                        SSL.setuphsts(self, kc_domain)
                    else:
                        Log.error(self, "HSTS is already configured for given "
                                        "site")
                    if not kcService.reload_service(self, 'nginx'):
                        Log.error(self, "service nginx reload failed. "
                                  "check issues with `nginx -t` command")
                else:
                    Log.error(self, "HTTPS is not configured for given "
                              "site")

            elif data['hsts'] is False:
                if os.path.isfile(("{0}/conf/nginx/hsts.conf")
                                  .format(kc_site_webroot)):
                    KCFileUtils.mvfile(self, "{0}/conf/nginx/hsts.conf"
                                       .format(kc_site_webroot),
                                       '{0}/conf/nginx/hsts.conf.disabled'
                                       .format(kc_site_webroot))
                    if not KCService.reload_service(self, 'nginx'):
                        Log.error(self, "service nginx reload failed. "
                                  "check issues with `nginx -t` command")
                else:
                    Log.error(self, "HSTS is not configured for given "
                              "site")
        if pargs.ngxblocker:
            if ngxblocker is True:
                setupngxblocker(self, kc_domain)
            elif ngxblocker is False:
                if os.path.isfile("{0}/conf/nginx/ngxblocker.conf"
                                  .format(kc_site_webroot)):
                    KCFileUtils.mvfile(
                        self,
                        "{0}/conf/nginx/ngxblocker.conf"
                        .format(kc_site_webroot),
                        "{0}/conf/nginx/ngxblocker.conf.disabled"
                        .format(kc_site_webroot))
            # Service Nginx Reload
            if not KCService.reload_service(self, 'nginx'):
                Log.error(self, "service nginx reload failed. "
                          "check issues with `nginx -t` command")

        if stype == oldsitetype and cache == oldcachetype:

            # Service Nginx Reload
            if not KCService.reload_service(self, 'nginx'):
                Log.error(self, "service nginx reload failed. "
                          "check issues with `nginx -t` command")

            updateSiteInfo(self, kc_domain, stype=stype, cache=cache,
                           ssl=(bool(check_site.is_ssl)),
                           php_version=check_php_version)

            Log.info(self, "Successfully updated site"
                     " http://{0}".format(kc_domain))
            return 0

        # if data['kc_db_name'] and not data['wp']:
        if 'kc_db_name' in data.keys() and not data['wp']:
            try:
                data = setupdatabase(self, data)
            except SiteError as e:
                Log.debug(self, str(e))
                Log.info(self, Log.FAIL + "Update site failed."
                         "Check the log for details:"
                         "`tail /var/log/kc/keepcloud.log` and please try again")
                return 1
            try:
                kcdbconfig = open("{0}/kc-config.php".format(kc_site_webroot),
                                  encoding='utf-8', mode='w')
                kcdbconfig.write("<?php \ndefine('DB_NAME', '{0}');"
                                 "\ndefine('DB_USER', '{1}'); "
                                 "\ndefine('DB_PASSWORD', '{2}');"
                                 "\ndefine('DB_HOST', '{3}');\n?>"
                                 .format(data['kc_db_name'],
                                         data['kc_db_user'],
                                         data['kc_db_pass'],
                                         data['kc_db_host']))
                kcdbconfig.close()
            except IOError as e:
                Log.debug(self, str(e))
                Log.debug(self, "creating kc-config.php failed.")
                Log.info(self, Log.FAIL + "Update site failed. "
                         "Check the log for details: "
                         "`tail /var/log/kc/keepcloud.log` and please try again")
                return 1

        # Setup WordPress if old sites are html/php/mysql sites
        if data['wp'] and oldsitetype in ['html', 'proxy', 'php', 'php72',
                                          'mysql', 'php73', 'php74', 'php80',
                                          'php81', ]:
            try:
                kc_wp_creds = setupwordpress(self, data)
            except SiteError as e:
                Log.debug(self, str(e))
                Log.info(self, Log.FAIL + "Update site failed."
                         "Check the log for details: "
                         "`tail /var/log/kc/keepcloud.log` and please try again")
                return 1

        # Uninstall unnecessary plugins
        if oldsitetype in ['wp', 'wpsubdir', 'wpsubdomain']:
            # Setup WordPress Network if update option is multisite
            # and oldsite is WordPress single site
            if data['multisite'] and oldsitetype == 'wp':
                try:
                    setupwordpressnetwork(self, data)
                except SiteError as e:
                    Log.debug(self, str(e))
                    Log.info(self, Log.FAIL + "Update site failed. "
                             "Check the log for details:"
                             " `tail /var/log/kc/keepcloud.log` "
                             "and please try again")
                    return 1

            if ((oldcachetype in ['wpsc', 'basic', 'wpredis', 'wprocket',
                                  'wpce'] and
                 (data['wpfc'])) or (oldsitetype == 'wp' and
                                     data['multisite'] and data['wpfc'])):
                try:
                    plugin_data_object = {
                        "log_level": "INFO",
                        "log_filesize": 5,
                        "enable_purge": 1,
                        "enable_map": "0",
                        "enable_log": 0,
                        "enable_stamp": 1,
                        "purge_homepage_on_new": 1,
                        "purge_homepage_on_edit": 1,
                        "purge_homepage_on_del": 1,
                        "purge_archive_on_new": 1,
                        "purge_archive_on_edit": 0,
                        "purge_archive_on_del": 0,
                        "purge_archive_on_new_comment": 0,
                        "purge_archive_on_deleted_comment": 0,
                        "purge_page_on_mod": 1,
                        "purge_page_on_new_comment": 1,
                        "purge_page_on_deleted_comment": 1,
                        "cache_method": "enable_fastcgi",
                        "purge_method": "get_request",
                        "redis_hostname": "127.0.0.1",
                                          "redis_port": "6379",
                                          "redis_prefix": "nginx-cache:"}
                    plugin_data = json.dumps(plugin_data_object)
                    setupwp_plugin(self, 'nginx-helper',
                                   'rt_wp_nginx_helper_options',
                                   plugin_data, data)
                except SiteError as e:
                    Log.debug(self, str(e))
                    Log.info(self, Log.FAIL + "Update nginx-helper "
                             "settings failed. "
                             "Check the log for details:"
                             " `tail /var/log/kc/keepcloud.log` "
                             "and please try again")
                    return 1

            elif ((oldcachetype in ['wpsc', 'basic', 'wpfc',
                                    'wprocket', 'wpce'] and
                   (data['wpredis'])) or (oldsitetype == 'wp' and
                                          data['multisite'] and
                                          data['wpredis'])):
                try:
                    plugin_data_object = {
                        "log_level": "INFO",
                        "log_filesize": 5,
                        "enable_purge": 1,
                        "enable_map": "0",
                        "enable_log": 0,
                        "enable_stamp": 1,
                        "purge_homepage_on_new": 1,
                        "purge_homepage_on_edit": 1,
                        "purge_homepage_on_del": 1,
                        "purge_archive_on_new": 1,
                        "purge_archive_on_edit": 0,
                        "purge_archive_on_del": 0,
                        "purge_archive_on_new_comment": 0,
                        "purge_archive_on_deleted_comment": 0,
                        "purge_page_on_mod": 1,
                        "purge_page_on_new_comment": 1,
                        "purge_page_on_deleted_comment": 1,
                        "cache_method": "enable_redis",
                        "purge_method": "get_request",
                        "redis_hostname": "127.0.0.1",
                                          "redis_port": "6379",
                                          "redis_prefix": "nginx-cache:"}
                    plugin_data = json.dumps(plugin_data_object)
                    setupwp_plugin(self, 'nginx-helper',
                                   'rt_wp_nginx_helper_options',
                                   plugin_data, data)
                except SiteError as e:
                    Log.debug(self, str(e))
                    Log.info(self, Log.FAIL + "Update nginx-helper "
                             "settings failed. "
                             "Check the log for details:"
                             " `tail /var/log/kc/keepcloud.log` "
                             "and please try again")
                    return 1
            else:
                try:
                    # disable nginx-helper
                    plugin_data_object = {
                        "log_level": "INFO",
                        "log_filesize": 5,
                        "enable_purge": 0,
                        "enable_map": 0,
                        "enable_log": 0,
                        "enable_stamp": 0,
                        "purge_homepage_on_new": 1,
                        "purge_homepage_on_edit": 1,
                        "purge_homepage_on_del": 1,
                        "purge_archive_on_new": 1,
                        "purge_archive_on_edit": 0,
                        "purge_archive_on_del": 0,
                        "purge_archive_on_new_comment": 0,
                        "purge_archive_on_deleted_comment": 0,
                        "purge_page_on_mod": 1,
                        "purge_page_on_new_comment": 1,
                        "purge_page_on_deleted_comment": 1,
                        "cache_method": "enable_redis",
                        "purge_method": "get_request",
                        "redis_hostname": "127.0.0.1",
                                          "redis_port": "6379",
                                          "redis_prefix": "nginx-cache:"}
                    plugin_data = json.dumps(plugin_data_object)
                    setupwp_plugin(
                        self, 'nginx-helper',
                        'rt_wp_nginx_helper_options', plugin_data, data)
                except SiteError as e:
                    Log.debug(self, str(e))
                    Log.info(self, Log.FAIL + "Update nginx-helper "
                             "settings failed. "
                             "Check the log for details:"
                             " `tail /var/log/kc/keepcloud.log` "
                             "and please try again")
                    return 1

            if ((oldcachetype in ['wpsc', 'basic',
                                  'wpfc', 'wprocket', 'wpredis'] and
                 (data['wpce'])) or (oldsitetype == 'wp' and
                                     data['multisite'] and
                                     data['wpce'])):
                try:
                    installwp_plugin(self, 'cache-enabler', data)
                    # setup cache-enabler
                    plugin_data_object = {
                        "expires": 24,
                        "new_post": 1,
                        "new_comment": 0,
                        "webp": 0,
                        "clear_on_upgrade": 1,
                        "compress": 0,
                        "excl_ids": "",
                        "excl_regexp": "",
                        "excl_cookies": "",
                        "incl_attributes": "",
                        "minify_html": 1}
                    plugin_data = json.dumps(plugin_data_object)
                    setupwp_plugin(self, 'cache-enabler',
                                   'cache-enabler', plugin_data, data)
                except SiteError as e:
                    Log.debug(self, str(e))
                    Log.info(self, Log.FAIL + "Update cache-enabler "
                             "settings failed. "
                             "Check the log for details:"
                             " `tail /var/log/kc/keepcloud.log` "
                             "and please try again")
                    return 1

            if oldcachetype == 'wpsc' and not data['wpsc']:
                try:
                    uninstallwp_plugin(self, 'wp-super-cache', data)
                except SiteError as e:
                    Log.debug(self, str(e))
                    Log.info(self, Log.FAIL + "Update site failed."
                             "Check the log for details:"
                             " `tail /var/log/kc/keepcloud.log` "
                             "and please try again")
                    return 1

            if oldcachetype == 'wpredis' and not data['wpredis']:
                try:
                    uninstallwp_plugin(self, 'redis-cache', data)
                except SiteError as e:
                    Log.debug(self, str(e))
                    Log.info(self, Log.FAIL + "Update site failed."
                             "Check the log for details:"
                             " `tail /var/log/kc/keepcloud.log` "
                             "and please try again")
                    return 1

        if oldcachetype != 'wpsc' and data['wpsc']:
            try:
                installwp_plugin(self, 'wp-super-cache', data)
            except SiteError as e:
                Log.debug(self, str(e))
                Log.info(self, Log.FAIL + "Update site failed."
                         "Check the log for details: "
                         "`tail /var/log/kc/keepcloud.log` and please try again")
                return 1

        if oldcachetype == 'wprocket' and not data['wprocket']:
            try:
                uninstallwp_plugin(self, 'wp-rocket', data)
            except SiteError as e:
                Log.debug(self, str(e))
                Log.info(self, Log.FAIL + "Update site failed."
                         "Check the log for details: "
                         "`tail /var/log/kc/keepcloud.log` and please try again")
                return 1

        if oldcachetype == 'wpce' and not data['wpce']:
            try:
                uninstallwp_plugin(self, 'cache-enabler', data)
            except SiteError as e:
                Log.debug(self, str(e))
                Log.info(self, Log.FAIL + "Update site failed."
                         "Check the log for details: "
                         "`tail /var/log/kc/keepcloud.log` and please try again")
                return 1

        # Service Nginx Reload
        if not KCService.reload_service(self, 'nginx'):
            Log.error(self, "service nginx reload failed. "
                      "check issues with `nginx -t` command")

        KCGit.add(self, ["/etc/nginx"],
                  msg="{0} updated with {1} {2}"
                  .format(kc_www_domain, stype, cache))
        # Setup Permissions for webroot
        try:
            setwebrootpermissions(self, data['webroot'])
        except SiteError as e:
            Log.debug(self, str(e))
            Log.info(self, Log.FAIL + "Update site failed."
                     "Check the log for details: "
                     "`tail /var/log/kc/keepcloud.log` and please try again")
            return 1

        if kc_auth and len(kc_auth):
            for msg in kc_auth:
                Log.info(self, Log.ENDC + msg)

        display_cache_settings(self, data)
        if data['wp'] and oldsitetype in ['html', 'php', 'mysql']:
            Log.info(self, "\n\n" + Log.ENDC + "WordPress admin user :"
                     " {0}".format(kc_wp_creds['wp_user']))
            Log.info(self, Log.ENDC + "WordPress admin password : {0}"
                     .format(kc_wp_creds['wp_pass']) + "\n\n")
        if oldsitetype in ['html', 'php'] and stype != 'php':
            updateSiteInfo(self, kc_domain, stype=stype, cache=cache,
                           db_name=data['kc_db_name'],
                           db_user=data['kc_db_user'],
                           db_password=data['kc_db_pass'],
                           db_host=data['kc_db_host'],
                           ssl=bool(check_site.is_ssl),
                           php_version=check_php_version)
        else:
            updateSiteInfo(self, kc_domain, stype=stype, cache=cache,
                           ssl=bool(check_site.is_ssl),
                           php_version=check_php_version)
        Log.info(self, "Successfully updated site"
                 " http://{0}".format(kc_domain))
        return 0
