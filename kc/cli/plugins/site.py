import glob
import os
import subprocess

from cement.core.controller import CementBaseController, expose
from kc.cli.plugins.site_functions import (
    check_domain_exists, deleteDB, deleteWebRoot, removeNginxConf, logwatch)
from kc.cli.plugins.sitedb import (deleteSiteInfo, getAllsites,
                                   getSiteInfo, updateSiteInfo)
from kc.cli.plugins.site_create import KCSiteCreateController
from kc.cli.plugins.site_update import KCSiteUpdateController
from kc.core.domainvalidate import KCDomain
from kc.core.fileutils import KCFileUtils
from kc.core.git import KCGit
from kc.core.logging import Log
from kc.core.services import KCService
from kc.core.shellexec import KCShellExec, CommandExecutionError
from kc.core.sslutils import SSL
from kc.core.variables import KCVar
from kc.core.acme import KCAcme


def kc_site_hook(app):
    from kc.core.database import init_db
    import kc.cli.plugins.models
    init_db(app)


class KCSiteController(CementBaseController):
    class Meta:
        label = 'site'
        stacked_on = 'base'
        stacked_type = 'nested'
        description = ('Performs website specific operations')
        arguments = [
            (['site_name'],
                dict(help='Website name', nargs='?')),
        ]
        usage = "kc site (command) <site_name> [options]"

    @expose(hide=True)
    def default(self):
        self.app.args.print_help()

    @expose(help="Enable site example.com")
    def enable(self):
        pargs = self.app.pargs
        if not pargs.site_name:
            try:
                while not pargs.site_name:
                    pargs.site_name = (input('Enter site name : ')
                                       .strip())
            except IOError as e:
                Log.debug(self, str(e))
                Log.error(self, 'could not input site name')

        pargs.site_name = pargs.site_name.strip()
        # validate domain name
        kc_domain = KCDomain.validate(self, pargs.site_name)

        # check if site exists
        if not check_domain_exists(self, kc_domain):
            Log.error(self, "site {0} does not exist".format(kc_domain))
        if os.path.isfile('/etc/nginx/sites-available/{0}'
                          .format(kc_domain)):
            Log.info(self, "Enable domain {0:10} \t".format(kc_domain), end='')
            KCFileUtils.create_symlink(self,
                                       ['/etc/nginx/sites-available/{0}'
                                        .format(kc_domain),
                                        '/etc/nginx/sites-enabled/{0}'
                                        .format(kc_domain)])
            KCGit.add(self, ["/etc/nginx"],
                      msg="Enabled {0} "
                      .format(kc_domain))
            updateSiteInfo(self, kc_domain, enabled=True)
            Log.info(self, "[" + Log.ENDC + "OK" + Log.OKBLUE + "]")
            if not KCService.reload_service(self, 'nginx'):
                Log.error(self, "service nginx reload failed. "
                          "check issues with `nginx -t` command")
        else:
            Log.error(self, 'nginx configuration file does not exist')

    @expose(help="Disable site example.com")
    def disable(self):
        pargs = self.app.pargs
        if not pargs.site_name:
            try:
                while not pargs.site_name:
                    pargs.site_name = (input('Enter site name : ')
                                       .strip())

            except IOError as e:
                Log.debug(self, str(e))
                Log.error(self, 'could not input site name')
        pargs.site_name = pargs.site_name.strip()
        kc_domain = KCDomain.validate(self, pargs.site_name)
        # check if site exists
        if not check_domain_exists(self, kc_domain):
            Log.error(self, "site {0} does not exist".format(kc_domain))

        if os.path.isfile('/etc/nginx/sites-available/{0}'
                          .format(kc_domain)):
            Log.info(self, "Disable domain {0:10} \t"
                     .format(kc_domain), end='')
            if not os.path.isfile('/etc/nginx/sites-enabled/{0}'
                                  .format(kc_domain)):
                Log.debug(self, "Site {0} already disabled".format(kc_domain))
                Log.info(self, "[" + Log.FAIL + "Failed" + Log.OKBLUE + "]")
            else:
                KCFileUtils.remove_symlink(self,
                                           '/etc/nginx/sites-enabled/{0}'
                                           .format(kc_domain))
                KCGit.add(self, ["/etc/nginx"],
                          msg="Disabled {0} "
                          .format(kc_domain))
                updateSiteInfo(self, kc_domain, enabled=False)
                Log.info(self, "[" + Log.ENDC + "OK" + Log.OKBLUE + "]")
                if not KCService.reload_service(self, 'nginx'):
                    Log.error(self, "service nginx reload failed. "
                              "check issues with `nginx -t` command")
        else:
            Log.error(self, "nginx configuration file does not exist")

    @expose(help="Get example.com information")
    def info(self):
        pargs = self.app.pargs
        if not pargs.site_name:
            try:
                while not pargs.site_name:
                    pargs.site_name = (input('Enter site name : ')
                                       .strip())
            except IOError as e:
                Log.debug(self, str(e))
                Log.error(self, 'could not input site name')
        pargs.site_name = pargs.site_name.strip()
        kc_domain = KCDomain.validate(self, pargs.site_name)
        (kc_domain_type, kc_root_domain) = KCDomain.getlevel(
            self, kc_domain)
        kc_db_name = ''
        kc_db_user = ''
        kc_db_pass = ''

        if not check_domain_exists(self, kc_domain):
            Log.error(self, "site {0} does not exist".format(kc_domain))
        if os.path.isfile('/etc/nginx/sites-available/{0}'
                          .format(kc_domain)):
            siteinfo = getSiteInfo(self, kc_domain)
            sitetype = siteinfo.site_type
            cachetype = siteinfo.cache_type
            kc_site_webroot = siteinfo.site_path
            access_log = (kc_site_webroot + '/logs/access.log')
            error_log = (kc_site_webroot + '/logs/error.log')
            kc_db_name = siteinfo.db_name
            kc_db_user = siteinfo.db_user
            kc_db_pass = siteinfo.db_password

            php_version = siteinfo.php_version

            ssl = ("enabled" if siteinfo.is_ssl else "disabled")
            if (ssl == "enabled"):
                sslprovider = "Lets Encrypt"
                sslexpiry = str(SSL.getexpirationdays(self, kc_domain))
            else:
                sslprovider = ''
                sslexpiry = ''
            data = dict(domain=kc_domain, domain_type=kc_domain_type,
                        webroot=kc_site_webroot,
                        accesslog=access_log, errorlog=error_log,
                        dbname=kc_db_name, dbuser=kc_db_user,
                        php_version=php_version,
                        dbpass=kc_db_pass,
                        ssl=ssl, sslprovider=sslprovider, sslexpiry=sslexpiry,
                        type=sitetype + " " + cachetype + " ({0})"
                        .format("enabled" if siteinfo.is_enabled else
                                "disabled"))
            self.app.render((data), 'siteinfo.mustache')
        else:
            Log.error(self, "nginx configuration file does not exist")

    @expose(help="Monitor example.com logs")
    def log(self):
        pargs = self.app.pargs
        pargs.site_name = pargs.site_name.strip()
        kc_domain = KCDomain.validate(self, pargs.site_name)
        kc_site_webroot = getSiteInfo(self, kc_domain).site_path

        if not check_domain_exists(self, kc_domain):
            Log.error(self, "site {0} does not exist".format(kc_domain))
        logfiles = glob.glob(kc_site_webroot + '/logs/*.log')
        if logfiles:
            logwatch(self, logfiles)

    @expose(help="Display Nginx configuration of example.com")
    def show(self):
        pargs = self.app.pargs
        if not pargs.site_name:
            try:
                while not pargs.site_name:
                    pargs.site_name = (input('Enter site name : ')
                                       .strip())
            except IOError as e:
                Log.debug(self, str(e))
                Log.error(self, 'could not input site name')
        # TODO Write code for kc site edit command here
        pargs.site_name = pargs.site_name.strip()
        kc_domain = KCDomain.validate(self, pargs.site_name)

        if not check_domain_exists(self, kc_domain):
            Log.error(self, "site {0} does not exist".format(kc_domain))

        if os.path.isfile('/etc/nginx/sites-available/{0}'
                          .format(kc_domain)):
            Log.info(self, "Display NGINX configuration for {0}"
                     .format(kc_domain))
            f = open('/etc/nginx/sites-available/{0}'.format(kc_domain),
                     encoding='utf-8', mode='r')
            text = f.read()
            Log.info(self, Log.ENDC + text)
            f.close()
        else:
            Log.error(self, "nginx configuration file does not exists")

    @expose(help="Change directory to site webroot")
    def cd(self):
        pargs = self.app.pargs
        if not pargs.site_name:
            try:
                while not pargs.site_name:
                    pargs.site_name = (input('Enter site name : ')
                                       .strip())
            except IOError as e:
                Log.debug(self, str(e))
                Log.error(self, 'Unable to read input, please try again')

        pargs.site_name = pargs.site_name.strip()
        kc_domain = KCDomain.validate(self, pargs.site_name)

        if not check_domain_exists(self, kc_domain):
            Log.error(self, "site {0} does not exist".format(kc_domain))

        kc_site_webroot = getSiteInfo(self, kc_domain).site_path
        if os.path.isdir(kc_site_webroot):
            KCFileUtils.chdir(self, kc_site_webroot)

        try:
            subprocess.call(['/bin/bash'])
        except OSError as e:
            Log.debug(self, "{0}{1}".format(e.errno, e.strerror))
        else:
            Log.error(self, "unable to change directory")


class KCSiteEditController(CementBaseController):
    class Meta:
        label = 'edit'
        stacked_on = 'site'
        stacked_type = 'nested'
        description = ('Edit Nginx configuration of site')
        arguments = [
            (['site_name'],
                dict(help='domain name for the site',
                     nargs='?')),
        ]

    @expose(hide=True)
    def default(self):
        pargs = self.app.pargs
        if not pargs.site_name:
            try:
                while not pargs.site_name:
                    pargs.site_name = (input('Enter site name : ')
                                       .strip())
            except IOError as e:
                Log.debug(self, str(e))
                Log.error(self, 'Unable to read input, Please try again')

        pargs.site_name = pargs.site_name.strip()
        kc_domain = KCDomain.validate(self, pargs.site_name)
        if not check_domain_exists(self, kc_domain):
            Log.error(self, "site {0} does not exist".format(kc_domain))

        if os.path.isfile('/etc/nginx/sites-available/{0}'
                          .format(kc_domain)):
            try:
                KCShellExec.invoke_editor(self, '/etc/nginx/sites-availa'
                                          'ble/{0}'.format(kc_domain))
            except CommandExecutionError as e:
                Log.debug(self, str(e))
                Log.error(self, "Failed invoke editor")
            if (KCGit.checkfilestatus(self, "/etc/nginx",
                                      '/etc/nginx/sites-available/{0}'
                                      .format(kc_domain))):
                KCGit.add(self, ["/etc/nginx"], msg="Edit website: {0}"
                          .format(kc_domain))
                # Reload NGINX
                if not KCService.reload_service(self, 'nginx'):
                    Log.error(self, "service nginx reload failed. "
                              "check issues with `nginx -t` command")
        else:
            Log.error(self, "nginx configuration file does not exists")


class KCSiteDeleteController(CementBaseController):
    class Meta:
        label = 'delete'
        stacked_on = 'site'
        stacked_type = 'nested'
        description = 'delete an existing website'
        arguments = [
            (['site_name'],
                dict(help='domain name to be deleted', nargs='?')),
            (['--no-prompt'],
                dict(help="doesnt ask permission for delete",
                     action='store_true')),
            (['-f', '--force'],
                dict(help="forcefully delete site and configuration",
                     action='store_true')),
            (['--all'],
                dict(help="delete files & db", action='store_true')),
            (['--db'],
                dict(help="delete db only", action='store_true')),
            (['--files'],
                dict(help="delete webroot only", action='store_true')),
        ]

    @expose(help="Delete website configuration and files")
    @expose(hide=True)
    def default(self):
        pargs = self.app.pargs
        if not pargs.site_name and not pargs.all:
            try:
                while not pargs.site_name:
                    pargs.site_name = (input('Enter site name : ')
                                       .strip())
            except IOError as e:
                Log.debug(self, str(e))
                Log.error(self, 'could not input site name')

        pargs.site_name = pargs.site_name.strip()
        kc_domain = KCDomain.validate(self, pargs.site_name)
        kc_db_name = ''
        kc_prompt = ''
        kc_nginx_prompt = ''
        mark_db_delete_prompt = False
        mark_webroot_delete_prompt = False
        mark_db_deleted = False
        mark_webroot_deleted = False
        if not check_domain_exists(self, kc_domain):
            Log.error(self, "site {0} does not exist".format(kc_domain))

        if ((not pargs.db) and (not pargs.files) and
                (not pargs.all)):
            pargs.all = True

        if pargs.force:
            pargs.no_prompt = True

        # Gather information from kc-db for kc_domain
        check_site = getSiteInfo(self, kc_domain)
        kc_site_type = check_site.site_type
        kc_site_webroot = check_site.site_path
        if kc_site_webroot == 'deleted':
            mark_webroot_deleted = True
        if kc_site_type in ['mysql', 'wp', 'wpsubdir', 'wpsubdomain']:
            kc_db_name = check_site.db_name
            kc_db_user = check_site.db_user
            if self.app.config.has_section('mysql'):
                kc_mysql_grant_host = self.app.config.get(
                    'mysql', 'grant-host')
            else:
                kc_mysql_grant_host = 'localhost'
            if kc_db_name == 'deleted':
                mark_db_deleted = True
            if pargs.all:
                pargs.db = True
                pargs.files = True
        else:
            if pargs.all:
                mark_db_deleted = True
                pargs.files = True

        # Delete website database
        if pargs.db:
            if kc_db_name != 'deleted' and kc_db_name != '':
                if not pargs.no_prompt:
                    kc_db_prompt = input('Are you sure, you want to delete'
                                         ' database [y/N]: ')
                else:
                    kc_db_prompt = 'Y'
                    mark_db_delete_prompt = True

                if kc_db_prompt == 'Y' or kc_db_prompt == 'y':
                    mark_db_delete_prompt = True
                    Log.info(self, "Deleting Database, {0}, user {1}"
                             .format(kc_db_name, kc_db_user))
                    deleteDB(self, kc_db_name, kc_db_user,
                             kc_mysql_grant_host, False)
                    updateSiteInfo(self, kc_domain,
                                   db_name='deleted',
                                   db_user='deleted',
                                   db_password='deleted')
                    mark_db_deleted = True
                    Log.info(self, "Deleted Database successfully.")
            else:
                mark_db_deleted = True
                Log.info(self, "Does not seems to have database for this site."
                         )

        # Delete webroot
        if pargs.files:
            if kc_site_webroot != 'deleted':
                if not pargs.no_prompt:
                    kc_web_prompt = input('Are you sure, you want to delete '
                                          'webroot [y/N]: ')
                else:
                    kc_web_prompt = 'Y'
                    mark_webroot_delete_prompt = True

                if kc_web_prompt == 'Y' or kc_web_prompt == 'y':
                    mark_webroot_delete_prompt = True
                    Log.info(self, "Deleting Webroot, {0}"
                             .format(kc_site_webroot))
                    deleteWebRoot(self, kc_site_webroot)
                    updateSiteInfo(self, kc_domain, webroot='deleted')
                    mark_webroot_deleted = True
                    Log.info(self, "Deleted webroot successfully")
            else:
                mark_webroot_deleted = True
                Log.info(self, "Webroot seems to be already deleted")

        if not pargs.force:
            if (mark_webroot_deleted and mark_db_deleted):
                # TODO Delete nginx conf
                removeNginxConf(self, kc_domain)
                deleteSiteInfo(self, kc_domain)
                KCAcme.removeconf(self, kc_domain)
                Log.info(self, "Deleted site {0}".format(kc_domain))
                # else:
                # Log.error(self, " site {0} does
                # not exists".format(kc_domain))
        else:
            if (mark_db_delete_prompt or mark_webroot_delete_prompt or
                    (mark_webroot_deleted and mark_db_deleted)):
                # TODO Delete nginx conf
                removeNginxConf(self, kc_domain)
                deleteSiteInfo(self, kc_domain)
                # To improve
                if not KCFileUtils.grepcheck(
                        self, '/var/www/22222/conf/nginx/ssl.conf', kc_domain):
                    KCAcme.removeconf(self, kc_domain)
                Log.info(self, "Deleted site {0}".format(kc_domain))


class KCSiteListController(CementBaseController):
    class Meta:
        label = 'list'
        stacked_on = 'site'
        stacked_type = 'nested'
        description = 'List websites'
        arguments = [
            (['--enabled'],
                dict(help='List enabled websites', action='store_true')),
            (['--disabled'],
                dict(help="List disabled websites", action='store_true')),
        ]

    @expose(help="Lists websites")
    def default(self):
        pargs = self.app.pargs
        sites = getAllsites(self)
        if not sites:
            pass

        if pargs.enabled:
            for site in sites:
                if site.is_enabled:
                    Log.info(self, "{0}".format(site.sitename))
        elif pargs.disabled:
            for site in sites:
                if not site.is_enabled:
                    Log.info(self, "{0}".format(site.sitename))
        else:
            for site in sites:
                Log.info(self, "{0}".format(site.sitename))


def load(app):
    # register the plugin class.. this only happens if the plugin is enabled
    app.handler.register(KCSiteController)
    app.handler.register(KCSiteDeleteController)
    app.handler.register(KCSiteUpdateController)
    app.handler.register(KCSiteCreateController)
    app.handler.register(KCSiteListController)
    app.handler.register(KCSiteEditController)
    # register a hook (function) to run after arguments are parsed.
    app.hook.register('post_argument_parsing', kc_site_hook)
