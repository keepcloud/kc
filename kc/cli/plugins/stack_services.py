import os

from cement.core.controller import CementBaseController, expose
from kc.core.logging import Log
from kc.core.services import KCService
from kc.core.variables import KCVar
from kc.core.fileutils import KCFileUtils


class KCStackStatusController(CementBaseController):
    class Meta:
        label = 'stack_services'
        stacked_on = 'stack'
        stacked_type = 'embedded'
        description = 'Check the stack status'

    @expose(help="Start stack services")
    def start(self):
        """Start services"""
        services = []
        kc_system = "/lib/systemd/system/"
        pargs = self.app.pargs
        if not (pargs.nginx or pargs.php or
                pargs.php72 or
                pargs.php73 or
                pargs.php74 or
                pargs.php80 or
                pargs.php81 or
                pargs.mysql or
                pargs.redis or
                pargs.fail2ban or
                pargs.proftpd or
                pargs.netdata or
                pargs.ufw):
            pargs.nginx = True
            pargs.php = True
            pargs.mysql = True
            pargs.fail2ban = True
            pargs.netdata = True
            pargs.ufw = True

        if pargs.nginx:
            if os.path.exists('{0}'.format(kc_system) + 'nginx.service'):
                services = services + ['nginx']
            else:
                Log.info(self, "Nginx is not installed")

        if pargs.php:
            if os.path.exists('{0}'.format(kc_system) + 'php7.2-fpm.service'):
                services = services + ['php7.2-fpm']
            else:
                Log.info(self, "PHP7.2-FPM is not installed")
            if os.path.exists('{0}'.format(kc_system) + 'php7.3-fpm.service'):
                services = services + ['php7.3-fpm']
            else:
                Log.info(self, "PHP7.3-FPM is not installed")
            if os.path.exists('{0}'.format(kc_system) + 'php7.4-fpm.service'):
                services = services + ['php7.4-fpm']
            else:
                Log.info(self, "PHP7.4-FPM is not installed")
            if os.path.exists('{0}'.format(kc_system) + 'php8.0-fpm.service'):
                services = services + ['php8.0-fpm']
            else:
                Log.info(self, "PHP8.0-FPM is not installed")
            if os.path.exists('{0}'.format(kc_system) + 'php8.1-fpm.service'):
                services = services + ['php8.1-fpm']
            else:
                Log.info(self, "PHP8.1-FPM is not installed")

        if pargs.php72:
            if os.path.exists('{0}'.format(kc_system) + 'php7.2-fpm.service'):
                services = services + ['php7.2-fpm']
            else:
                Log.info(self, "PHP7.2-FPM is not installed")

        if pargs.php73:
            if os.path.exists('{0}'.format(kc_system) + 'php7.3-fpm.service'):
                services = services + ['php7.3-fpm']
            else:
                Log.info(self, "PHP7.3-FPM is not installed")

        if pargs.php74:
            if os.path.exists('{0}'.format(kc_system) + 'php7.4-fpm.service'):
                services = services + ['php7.4-fpm']
            else:
                Log.info(self, "PHP7.4-FPM is not installed")

        if pargs.php80:
            if os.path.exists('{0}'.format(kc_system) + 'php8.0-fpm.service'):
                services = services + ['php8.0-fpm']
            else:
                Log.info(self, "PHP8.0-FPM is not installed")

        if pargs.php81:
            if os.path.exists('{0}'.format(kc_system) + 'php8.1-fpm.service'):
                services = services + ['php8.1-fpm']
            else:
                Log.info(self, "PHP8.1-FPM is not installed")

        if pargs.mysql:
            if ((KCVar.kc_mysql_host == "localhost") or
                    (KCVar.kc_mysql_host == "127.0.0.1")):
                if os.path.exists('/lib/systemd/system/mariadb.service'):
                    services = services + ['mariadb']
                else:
                    Log.info(self, "MySQL is not installed")
            else:
                Log.warn(self, "Remote MySQL found, "
                         "Unable to check MySQL service status")

        if pargs.redis:
            if os.path.exists('{0}'.format(kc_system) +
                              'redis-server.service'):
                services = services + ['redis-server']
            else:
                Log.info(self, "Redis server is not installed")

        if pargs.fail2ban:
            if os.path.exists('{0}'.format(kc_system) + 'fail2ban.service'):
                services = services + ['fail2ban']
            else:
                Log.info(self, "fail2ban is not installed")

        # proftpd
        if pargs.proftpd:
            if os.path.exists('/etc/init.d/proftpd'):
                services = services + ['proftpd']
            else:
                Log.info(self, "ProFTPd is not installed")

        # netdata
        if pargs.netdata:
            if os.path.exists('{0}'.format(kc_system) + 'netdata.service'):
                services = services + ['netdata']
            else:
                Log.info(self, "Netdata is not installed")

        for service in services:
            Log.debug(self, "Starting service: {0}".format(service))
            KCService.start_service(self, service)

    @expose(help="Stop stack services")
    def stop(self):
        """Stop services"""
        services = []
        kc_system = "/lib/systemd/system/"
        pargs = self.app.pargs
        if not (pargs.nginx or pargs.php or
                pargs.php72 or pargs.php73 or
                pargs.php74 or pargs.php80 or pargs.php81 or
                pargs.mysql or
                pargs.fail2ban or
                pargs.netdata or
                pargs.proftpd or
                pargs.redis):
            pargs.nginx = True
            pargs.php = True
            pargs.mysql = True

        if pargs.nginx:
            if os.path.exists('{0}'.format(kc_system) + 'nginx.service'):
                services = services + ['nginx']
            else:
                Log.info(self, "Nginx is not installed")

        if pargs.php:
            if os.path.exists('{0}'.format(kc_system) + 'php7.2-fpm.service'):
                services = services + ['php7.2-fpm']
            else:
                Log.info(self, "PHP7.2-FPM is not installed")
            if os.path.exists('{0}'.format(kc_system) + 'php7.3-fpm.service'):
                services = services + ['php7.3-fpm']
            else:
                Log.info(self, "PHP7.3-FPM is not installed")
            if os.path.exists('{0}'.format(kc_system) + 'php7.4-fpm.service'):
                services = services + ['php7.4-fpm']
            else:
                Log.info(self, "PHP7.4-FPM is not installed")

        if pargs.php72:
            if os.path.exists('{0}'.format(kc_system) + 'php7.2-fpm.service'):
                services = services + ['php7.2-fpm']
            else:
                Log.info(self, "PHP7.2-FPM is not installed")

        if pargs.php73:
            if os.path.exists('{0}'.format(kc_system) + 'php7.3-fpm.service'):
                services = services + ['php7.3-fpm']
            else:
                Log.info(self, "PHP7.3-FPM is not installed")

        if pargs.php74:
            if os.path.exists('{0}'.format(kc_system) + 'php7.4-fpm.service'):
                services = services + ['php7.4-fpm']
            else:
                Log.info(self, "PHP7.4-FPM is not installed")

        if pargs.php80:
            if os.path.exists('{0}'.format(kc_system) + 'php8.0-fpm.service'):
                services = services + ['php8.0-fpm']
            else:
                Log.info(self, "PHP8.0-FPM is not installed")

        if pargs.php81:
            if os.path.exists('{0}'.format(kc_system) + 'php8.1-fpm.service'):
                services = services + ['php8.1-fpm']
            else:
                Log.info(self, "PHP8.1-FPM is not installed")

        if pargs.mysql:
            if ((KCVar.kc_mysql_host == "localhost") or
                    (KCVar.kc_mysql_host == "127.0.0.1")):
                if os.path.exists('/lib/systemd/system/mariadb.service'):
                    services = services + ['mariadb']
                else:
                    Log.info(self, "MySQL is not installed")
            else:
                Log.warn(self, "Remote MySQL found, "
                         "Unable to check MySQL service status")

        if pargs.redis:
            if os.path.exists('{0}'.format(kc_system) +
                              'redis-server.service'):
                services = services + ['redis-server']
            else:
                Log.info(self, "Redis server is not installed")

        if pargs.fail2ban:
            if os.path.exists('{0}'.format(kc_system) + 'fail2ban.service'):
                services = services + ['fail2ban']
            else:
                Log.info(self, "fail2ban is not installed")

        # proftpd
        if pargs.proftpd:
            if os.path.exists('/etc/init.d/proftpd'):
                services = services + ['proftpd']
            else:
                Log.info(self, "ProFTPd is not installed")

        # netdata
        if pargs.netdata:
            if os.path.exists('{0}'.format(kc_system) + 'netdata.service'):
                services = services + ['netdata']
            else:
                Log.info(self, "Netdata is not installed")

        for service in services:
            Log.debug(self, "Stopping service: {0}".format(service))
            KCService.stop_service(self, service)

    @expose(help="Restart stack services")
    def restart(self):
        """Restart services"""
        services = []
        kc_system = "/lib/systemd/system/"
        pargs = self.app.pargs
        if not (pargs.nginx or pargs.php or
                pargs.php72 or pargs.php73 or
                pargs.php74 or pargs.php80 or pargs.php81 or
                pargs.mysql or
                pargs.netdata or
                pargs.proftpd or
                pargs.redis or
                pargs.fail2ban):
            pargs.nginx = True
            pargs.php = True
            pargs.mysql = True
            pargs.netdata = True

        if pargs.nginx:
            if os.path.exists('{0}'.format(kc_system) + 'nginx.service'):
                services = services + ['nginx']
            else:
                Log.info(self, "Nginx is not installed")

        if pargs.php:
            if os.path.exists('{0}'.format(kc_system) + 'php7.2-fpm.service'):
                services = services + ['php7.2-fpm']
            else:
                Log.info(self, "PHP7.2-FPM is not installed")
            if os.path.exists('{0}'.format(kc_system) + 'php7.3-fpm.service'):
                services = services + ['php7.3-fpm']
            else:
                Log.info(self, "PHP7.3-FPM is not installed")
            if os.path.exists('{0}'.format(kc_system) + 'php7.4-fpm.service'):
                services = services + ['php7.4-fpm']
            else:
                Log.info(self, "PHP8.0-FPM is not installed")
            if os.path.exists('{0}'.format(kc_system) + 'php8.0-fpm.service'):
                services = services + ['php8.0-fpm']
            else:
                Log.info(self, "PHP8.1-FPM is not installed")
            if os.path.exists('{0}'.format(kc_system) + 'php8.1-fpm.service'):
                services = services + ['php8.1-fpm']
            else:
                Log.info(self, "PHP7.4-FPM is not installed")

        if pargs.php72:
            if os.path.exists('{0}'.format(kc_system) + 'php7.2-fpm.service'):
                services = services + ['php7.2-fpm']
            else:
                Log.info(self, "PHP7.2-FPM is not installed")

        if pargs.php73:
            if os.path.exists('{0}'.format(kc_system) + 'php7.3-fpm.service'):
                services = services + ['php7.3-fpm']
            else:
                Log.info(self, "PHP7.3-FPM is not installed")

        if pargs.php74:
            if os.path.exists('{0}'.format(kc_system) + 'php7.4-fpm.service'):
                services = services + ['php7.4-fpm']
            else:
                Log.info(self, "PHP7.4-FPM is not installed")

        if pargs.php80:
            if os.path.exists('{0}'.format(kc_system) + 'php8.0-fpm.service'):
                services = services + ['php8.0-fpm']
            else:
                Log.info(self, "PHP8.0-FPM is not installed")

        if pargs.php81:
            if os.path.exists('{0}'.format(kc_system) + 'php8.1-fpm.service'):
                services = services + ['php8.1-fpm']
            else:
                Log.info(self, "PHP8.1-FPM is not installed")

        if pargs.mysql:
            if ((KCVar.kc_mysql_host == "localhost") or
                    (KCVar.kc_mysql_host == "127.0.0.1")):
                if os.path.exists('/lib/systemd/system/mariadb.service'):
                    services = services + ['mariadb']
                else:
                    Log.info(self, "MySQL is not installed")
            else:
                Log.warn(self, "Remote MySQL found, "
                         "Unable to check MySQL service status")

        if pargs.redis:
            if os.path.exists('{0}'.format(kc_system) +
                              'redis-server.service'):
                services = services + ['redis-server']
            else:
                Log.info(self, "Redis server is not installed")

        if pargs.fail2ban:
            if os.path.exists('{0}'.format(kc_system) + 'fail2ban.service'):
                services = services + ['fail2ban']
            else:
                Log.info(self, "fail2ban is not installed")

        # proftpd
        if pargs.proftpd:
            if os.path.exists('/etc/init.d/proftpd'):
                services = services + ['proftpd']
            else:
                Log.info(self, "ProFTPd is not installed")

        # netdata
        if pargs.netdata:
            if os.path.exists('{0}'.format(kc_system) + 'netdata.service'):
                services = services + ['netdata']
            else:
                Log.info(self, "Netdata is not installed")

        for service in services:
            Log.debug(self, "Restarting service: {0}".format(service))
            KCService.restart_service(self, service)

    @expose(help="Get stack status")
    def status(self):
        """Status of services"""
        services = []
        kc_system = "/lib/systemd/system/"
        pargs = self.app.pargs
        if not (pargs.nginx or pargs.php or
                pargs.php72 or
                pargs.php73 or
                pargs.php74 or
                pargs.php80 or
                pargs.php81 or
                pargs.mysql or
                pargs.netdata or
                pargs.proftpd or
                pargs.redis or
                pargs.fail2ban):
            pargs.nginx = True
            pargs.php = True
            pargs.mysql = True
            pargs.fail2ban = True
            pargs.netdata = True
            pargs.ufw = True

        if pargs.nginx:
            if os.path.exists('{0}'.format(kc_system) + 'nginx.service'):
                services = services + ['nginx']
            else:
                Log.info(self, "Nginx is not installed")

        if pargs.php:
            if os.path.exists('{0}'.format(kc_system) + 'php7.2-fpm.service'):
                services = services + ['php7.2-fpm']
            else:
                Log.info(self, "PHP7.2-FPM is not installed")
            if os.path.exists('{0}'.format(kc_system) + 'php7.3-fpm.service'):
                services = services + ['php7.3-fpm']
            else:
                Log.info(self, "PHP7.3-FPM is not installed")
            if os.path.exists('{0}'.format(kc_system) + 'php7.4-fpm.service'):
                services = services + ['php7.4-fpm']
            else:
                Log.info(self, "PHP7.4-FPM is not installed")
            if os.path.exists('{0}'.format(kc_system) + 'php8.0-fpm.service'):
                services = services + ['php8.0-fpm']
            else:
                Log.info(self, "PHP8.0-FPM is not installed")
            if os.path.exists('{0}'.format(kc_system) + 'php8.1-fpm.service'):
                services = services + ['php8.1-fpm']
            else:
                Log.info(self, "PHP8.1-FPM is not installed")

        if pargs.php72:
            if os.path.exists('{0}'.format(kc_system) + 'php7.2-fpm.service'):
                services = services + ['php7.2-fpm']
            else:
                Log.info(self, "PHP7.2-FPM is not installed")

        if pargs.php73:
            if os.path.exists('{0}'.format(kc_system) + 'php7.3-fpm.service'):
                services = services + ['php7.3-fpm']
            else:
                Log.info(self, "PHP7.3-FPM is not installed")

        if pargs.php74:
            if os.path.exists('{0}'.format(kc_system) + 'php7.4-fpm.service'):
                services = services + ['php7.4-fpm']
            else:
                Log.info(self, "PHP7.4-FPM is not installed")

        if pargs.php80:
            if os.path.exists('{0}'.format(kc_system) + 'php8.0-fpm.service'):
                services = services + ['php8.0-fpm']
            else:
                Log.info(self, "PHP8.0-FPM is not installed")

        if pargs.php81:
            if os.path.exists('{0}'.format(kc_system) + 'php8.1-fpm.service'):
                services = services + ['php8.1-fpm']
            else:
                Log.info(self, "PHP8.1-FPM is not installed")

        if pargs.mysql:
            if ((KCVar.kc_mysql_host == "localhost") or
                    (KCVar.kc_mysql_host == "127.0.0.1")):
                if os.path.exists('/lib/systemd/system/mariadb.service'):
                    services = services + ['mariadb']
                else:
                    Log.info(self, "MySQL is not installed")
            else:
                Log.warn(self, "Remote MySQL found, "
                         "Unable to check MySQL service status")

        if pargs.redis:
            if os.path.exists('{0}'.format(kc_system) +
                              'redis-server.service'):
                services = services + ['redis-server']
            else:
                Log.info(self, "Redis server is not installed")

        if pargs.fail2ban:
            if os.path.exists('{0}'.format(kc_system) + 'fail2ban.service'):
                services = services + ['fail2ban']
            else:
                Log.info(self, "fail2ban is not installed")

        # proftpd
        if pargs.proftpd:
            if os.path.exists('/etc/init.d/proftpd'):
                services = services + ['proftpd']
            else:
                Log.info(self, "ProFTPd is not installed")

        # netdata
        if pargs.netdata:
            if os.path.exists('{0}'.format(kc_system) + 'netdata.service'):
                services = services + ['netdata']
            else:
                Log.info(self, "Netdata is not installed")

        # UFW
        if pargs.ufw:
            if os.path.exists('/usr/sbin/ufw'):
                if KCFileUtils.grepcheck(
                        self, '/etc/ufw/ufw.conf', 'ENABLED=yes'):
                    Log.info(self, "UFW Firewall is enabled")
                else:
                    Log.info(self, "UFW Firewall is disabled")
            else:
                Log.info(self, "UFW is not installed")

        for service in services:
            if KCService.get_service_status(self, service):
                Log.info(self, "{0:10}:  {1}".format(service, "Running"))

    @expose(help="Reload stack services")
    def reload(self):
        """Reload service"""
        services = []
        kc_system = "/lib/systemd/system/"
        pargs = self.app.pargs
        if not (pargs.nginx or pargs.php or
                pargs.php72 or pargs.php73 or
                pargs.php74 or pargs.php80 or pargs.php81 or
                pargs.mysql or
                pargs.netdata or
                pargs.proftpd or
                pargs.redis or
                pargs.fail2ban):
            pargs.nginx = True
            pargs.php = True
            pargs.mysql = True
            pargs.fail2ban = True

        if pargs.nginx:
            if os.path.exists('{0}'.format(kc_system) + 'nginx.service'):
                services = services + ['nginx']
            else:
                Log.info(self, "Nginx is not installed")

        if pargs.php:
            if os.path.exists('{0}'.format(kc_system) + 'php7.2-fpm.service'):
                services = services + ['php7.2-fpm']
            else:
                Log.info(self, "PHP7.2-FPM is not installed")
            if os.path.exists('{0}'.format(kc_system) + 'php7.3-fpm.service'):
                services = services + ['php7.3-fpm']
            else:
                Log.info(self, "PHP7.3-FPM is not installed")
            if os.path.exists('{0}'.format(kc_system) + 'php7.4-fpm.service'):
                services = services + ['php7.4-fpm']
            else:
                Log.info(self, "PHP7.4-FPM is not installed")
            if os.path.exists('{0}'.format(kc_system) + 'php8.0-fpm.service'):
                services = services + ['php8.0-fpm']
            else:
                Log.info(self, "PHP8.0-FPM is not installed")
            if os.path.exists('{0}'.format(kc_system) + 'php8.1-fpm.service'):
                services = services + ['php8.1-fpm']
            else:
                Log.info(self, "PHP8.1-FPM is not installed")

        if pargs.php72:
            if os.path.exists('{0}'.format(kc_system) + 'php7.2-fpm.service'):
                services = services + ['php7.2-fpm']
            else:
                Log.info(self, "PHP7.2-FPM is not installed")

        if pargs.php73:
            if os.path.exists('{0}'.format(kc_system) + 'php7.3-fpm.service'):
                services = services + ['php7.3-fpm']
            else:
                Log.info(self, "PHP7.3-FPM is not installed")

        if pargs.php74:
            if os.path.exists('{0}'.format(kc_system) + 'php7.4-fpm.service'):
                services = services + ['php7.4-fpm']
            else:
                Log.info(self, "PHP7.4-FPM is not installed")

        if pargs.php80:
            if os.path.exists('{0}'.format(kc_system) + 'php8.0-fpm.service'):
                services = services + ['php8.0-fpm']
            else:
                Log.info(self, "PHP8.0-FPM is not installed")

        if pargs.php81:
            if os.path.exists('{0}'.format(kc_system) + 'php8.1-fpm.service'):
                services = services + ['php8.1-fpm']
            else:
                Log.info(self, "PHP8.1-FPM is not installed")

        if pargs.mysql:
            if ((KCVar.kc_mysql_host == "localhost") or
                    (KCVar.kc_mysql_host == "127.0.0.1")):
                if os.path.exists('/lib/systemd/system/mariadb.service'):
                    services = services + ['mysql']
                else:
                    Log.info(self, "MySQL is not installed")
            else:
                Log.warn(self, "Remote MySQL found, "
                         "Unable to check MySQL service status")

        if pargs.redis:
            if os.path.exists('{0}'.format(kc_system) +
                              'redis-server.service'):
                services = services + ['redis-server']
            else:
                Log.info(self, "Redis server is not installed")

        if pargs.fail2ban:
            if os.path.exists('{0}'.format(kc_system) + 'fail2ban.service'):
                services = services + ['fail2ban']
            else:
                Log.info(self, "fail2ban is not installed")

        # proftpd
        if pargs.proftpd:
            if os.path.exists('/etc/init.d/proftpd'):
                services = services + ['proftpd']
            else:
                Log.info(self, "ProFTPd is not installed")

        # netdata
        if pargs.netdata:
            if os.path.exists('{0}'.format(kc_system) + 'netdata.service'):
                services = services + ['netdata']
            else:
                Log.info(self, "Netdata is not installed")

        for service in services:
            Log.debug(self, "Reloading service: {0}".format(service))
            KCService.reload_service(self, service)
