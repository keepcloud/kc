"""Stack Plugin for KeepCloud"""

import os

from cement.core.controller import CementBaseController, expose

from kc.cli.plugins.stack_migrate import KCStackMigrateController
from kc.cli.plugins.stack_pref import post_pref, pre_pref, pre_stack
from kc.cli.plugins.stack_services import KCStackStatusController
from kc.cli.plugins.stack_upgrade import KCStackUpgradeController
from kc.core.aptget import KCAptGet
from kc.core.download import KCDownload
from kc.core.fileutils import KCFileUtils
from kc.core.logging import Log
from kc.core.mysql import KCMysql
from kc.core.services import KCService
from kc.core.shellexec import KCShellExec
from kc.core.variables import KCVar


def kc_stack_hook(app):
    pass


class KCStackController(CementBaseController):
    class Meta:
        label = 'stack'
        stacked_on = 'base'
        stacked_type = 'nested'
        description = 'Stack command manages stack operations'
        arguments = [
            (['--all'],
                dict(help='Install all stacks at once', action='store_true')),
            (['--web'],
                dict(help='Install web stack', action='store_true')),
            (['--admin'],
                dict(help='Install admin tools stack', action='store_true')),
            (['--security'],
             dict(help='Install security tools stack', action='store_true')),
            (['--nginx'],
                dict(help='Install Nginx stack', action='store_true')),
            (['--php'],
                dict(help='Install PHP 7.2 stack', action='store_true')),
            (['--php72'],
                dict(help='Install PHP 7.2 stack', action='store_true')),
            (['--php73'],
                dict(help='Install PHP 7.3 stack', action='store_true')),
            (['--php74'],
                dict(help='Install PHP 7.4 stack', action='store_true')),
            (['--php80'],
                dict(help='Install PHP 8.0 stack', action='store_true')),
            (['--php81'],
                dict(help='Install PHP 8.1 stack', action='store_true')),
            (['--mysql'],
                dict(help='Install MySQL stack', action='store_true')),
            (['--mariadb'],
                dict(help='Install MySQL stack alias', action='store_true')),
            (['--mysqlclient'],
                dict(help='Install MySQL client for remote MySQL server',
                     action='store_true')),
            (['--mysqltuner'],
                dict(help='Install MySQLTuner stack', action='store_true')),
            (['--wpcli'],
                dict(help='Install WPCLI stack', action='store_true')),
            (['--phpmyadmin'],
                dict(help='Install PHPMyAdmin stack', action='store_true')),
            (['--composer'],
                dict(help='Install Composer stack', action='store_true')),
            (['--netdata'],
                dict(help='Install Netdata monitoring suite',
                     action='store_true')),
            (['--dashboard'],
                dict(help='Install KeepCloud dashboard', action='store_true')),
            (['--extplorer'],
                dict(help='Install eXtplorer file manager',
                     action='store_true')),
            (['--adminer'],
                dict(help='Install Adminer stack', action='store_true')),
            (['--fail2ban'],
                dict(help='Install Fail2ban stack', action='store_true')),
            (['--clamav'],
                dict(help='Install ClamAV stack', action='store_true')),
            (['--ufw'],
                dict(help='Install UFW stack', action='store_true')),
            (['--sendmail'],
                dict(help='Install Sendmail stack', action='store_true')),
            (['--utils'],
                dict(help='Install Utils stack', action='store_true')),
            (['--redis'],
                dict(help='Install Redis', action='store_true')),
            (['--phpredisadmin'],
                dict(help='Install phpRedisAdmin', action='store_true')),
            (['--proftpd'],
                dict(help='Install ProFTPd', action='store_true')),
            (['--ngxblocker'],
                dict(help='Install Nginx Ultimate Bad Bot Blocker',
                     action='store_true')),
            (['--cheat'],
                dict(help='Install cheat.sh', action='store_true')),
            (['--nanorc'],
                dict(help='Install nanorc syntax highlighting',
                     action='store_true')),
            (['--force'],
                dict(help='Force install/remove/purge without prompt',
                     action='store_true')),
        ]
        usage = "kc stack (command) [options]"

    @expose(hide=True)
    def default(self):
        """default action of kc stack command"""
        self.app.args.print_help()

    @expose(help="Install packages")
    def install(self, packages=[], apt_packages=[], disp_msg=True):
        """Start installation of packages"""
        self.msg = []
        pargs = self.app.pargs

        try:
            # Default action for stack installation
            if not (pargs.web or pargs.admin or pargs.nginx or
                    pargs.php or pargs.php72 or pargs.php73 or pargs.php74 or
                    pargs.php80 or pargs.php81 or
                    pargs.mysql or pargs.wpcli or pargs.phpmyadmin or
                    pargs.composer or pargs.netdata or pargs.composer or
                    pargs.dashboard or pargs.fail2ban or pargs.security or
                    pargs.mysqlclient or pargs.mysqltuner or
                    pargs.admin or pargs.adminer or
                    pargs.utils or pargs.redis or pargs.mariadb or
                    pargs.proftpd or pargs.extplorer or
                    pargs.clamav or pargs.cheat or pargs.nanorc or
                    pargs.ufw or pargs.ngxblocker or
                    pargs.phpredisadmin or pargs.sendmail or pargs.all):
                pargs.web = True
                pargs.admin = True
                pargs.fail2ban = True

            if pargs.php:
                pargs.php80 = True

            if pargs.mariadb:
                pargs.mysql = True

            if pargs.all:
                pargs.web = True
                pargs.admin = True
                pargs.php73 = True
                pargs.php74 = True
                pargs.php80 = True
                pargs.php81 = True
                pargs.redis = True
                pargs.proftpd = True

            if pargs.web:
                if self.app.config.has_section('php'):
                    config_php_ver = self.app.config.get(
                        'php', 'version')
                if config_php_ver == '7.2':
                    pargs.php72 = True
                elif config_php_ver == '7.3':
                    pargs.php73 = True
                elif config_php_ver == '7.4':
                    pargs.php74 = True
                elif config_php_ver == '8.0':
                    pargs.php80 = True
                elif config_php_ver == '8.1':
                    pargs.php81 = True
                else:
                    pargs.php80 = True
                pargs.nginx = True
                pargs.mysql = True
                pargs.wpcli = True
                pargs.sendmail = True

            if pargs.admin:
                pargs.web = True
                pargs.adminer = True
                pargs.phpmyadmin = True
                pargs.composer = True
                pargs.utils = True
                pargs.netdata = True
                pargs.dashboard = True
                pargs.phpredisadmin = True
                pargs.extplorer = True
                pargs.cheat = True
                pargs.nanorc = True

            if pargs.security:
                pargs.fail2ban = True
                pargs.clamav = True
                pargs.ngxblocker = True

            # Nginx
            if pargs.nginx:
                Log.debug(self, "Setting apt_packages variable for Nginx")
                if not KCAptGet.is_exec(self, 'nginx'):
                    apt_packages = apt_packages + KCVar.kc_nginx
                else:
                    Log.debug(self, "Nginx already installed")

            # Redis
            if pargs.redis:
                if not KCAptGet.is_installed(self, 'redis-server'):
                    apt_packages = apt_packages + KCVar.kc_redis

                else:
                    Log.debug(self, "Redis already installed")

            # PHP 7.2
            if pargs.php72:
                Log.debug(self, "Setting apt_packages variable for PHP 7.2")
                if not (KCAptGet.is_installed(self, 'php7.2-fpm')):
                    apt_packages = (apt_packages + KCVar.kc_php72 +
                                    KCVar.kc_php_extra)
                else:
                    Log.debug(self, "PHP 7.2 already installed")
                    Log.info(self, "PHP 7.2 already installed")

            # PHP 7.3
            if pargs.php73:
                Log.debug(self, "Setting apt_packages variable for PHP 7.3")
                if not KCAptGet.is_installed(self, 'php7.3-fpm'):
                    apt_packages = (apt_packages + KCVar.kc_php73 +
                                    KCVar.kc_php_extra)
                else:
                    Log.debug(self, "PHP 7.3 already installed")
                    Log.info(self, "PHP 7.3 already installed")

            # PHP 7.4
            if pargs.php74:
                Log.debug(self, "Setting apt_packages variable for PHP 7.4")
                if not KCAptGet.is_installed(self, 'php7.4-fpm'):
                    apt_packages = (apt_packages + KCVar.kc_php74 +
                                    KCVar.kc_php_extra)
                else:
                    Log.debug(self, "PHP 7.4 already installed")
                    Log.info(self, "PHP 7.4 already installed")

            # PHP 8.0
            if pargs.php80:
                Log.debug(self, "Setting apt_packages variable for PHP 8.0")
                if not KCAptGet.is_installed(self, 'php8.0-fpm'):
                    apt_packages = (apt_packages + KCVar.kc_php80 +
                                    KCVar.kc_php_extra)
                else:
                    Log.debug(self, "PHP 8.0 already installed")
                    Log.info(self, "PHP 8.0 already installed")

            # PHP 8.1
            if pargs.php81:
                Log.debug(self, "Setting apt_packages variable for PHP 8.1")
                if not kcAptGet.is_installed(self, 'php8.1-fpm'):
                    apt_packages = (apt_packages + KCVar.kc_php81 +
                                    KCVar.kc_php_extra)
                else:
                    Log.debug(self, "PHP 8.1 already installed")
                    Log.info(self, "PHP 8.1 already installed")

            # MariaDB 10.3
            if pargs.mysql:
                pargs.mysqltuner = True
                Log.debug(self, "Setting apt_packages variable for MySQL")
                if not KCShellExec.cmd_exec(self, "mysqladmin ping"):
                    apt_packages = apt_packages + KCVar.kc_mysql
                else:
                    Log.debug(self, "MySQL already installed and alive")
                    Log.info(self, "MySQL already installed and alive")

            # mysqlclient
            if pargs.mysqlclient:
                Log.debug(self, "Setting apt_packages variable "
                          "for MySQL Client")
                if not KCShellExec.cmd_exec(self, "mysqladmin ping"):
                    apt_packages = apt_packages + KCVar.kc_mysql_client
                else:
                    Log.debug(self, "MySQL already installed and alive")
                    Log.info(self, "MySQL already installed and alive")

            # WP-CLI
            if pargs.wpcli:
                Log.debug(self, "Setting packages variable for WP-CLI")
                if not KCAptGet.is_exec(self, 'wp'):
                    packages = packages + [["https://github.com/wp-cli/wp-cli/"
                                            "releases/download/v{0}/"
                                            "wp-cli-{0}.phar"
                                            "".format(KCVar.kc_wp_cli),
                                            "/usr/local/bin/wp",
                                            "WP-CLI"]]
                else:
                    Log.debug(self, "WP-CLI is already installed")
                    Log.info(self, "WP-CLI is already installed")

            # fail2ban
            if pargs.fail2ban:
                Log.debug(self, "Setting apt_packages variable for Fail2ban")
                if not KCAptGet.is_installed(self, 'fail2ban'):
                    apt_packages = apt_packages + KCVar.kc_fail2ban
                else:
                    Log.debug(self, "Fail2ban already installed")
                    Log.info(self, "Fail2ban already installed")

            # ClamAV
            if pargs.clamav:
                Log.debug(self, "Setting apt_packages variable for ClamAV")
                if not KCAptGet.is_installed(self, 'clamav'):
                    apt_packages = apt_packages + KCVar.kc_clamav
                else:
                    Log.debug(self, "ClamAV already installed")
                    Log.info(self, "ClamAV already installed")

            # UFW
            if pargs.ufw:
                Log.debug(self, "Setting apt_packages variable for UFW")
                apt_packages = apt_packages + ["ufw"]

            # sendmail
            if pargs.sendmail:
                Log.debug(self, "Setting apt_packages variable for Sendmail")
                if (not KCAptGet.is_installed(self, 'sendmail') and
                        not KCAptGet.is_installed(self, 'postfix')):
                    apt_packages = apt_packages + ["sendmail"]
                else:
                    if KCAptGet.is_installed(self, 'sendmail'):
                        Log.debug(self, "Sendmail already installed")
                        Log.info(self, "Sendmail already installed")
                    else:
                        Log.debug(
                            self, "Another mta (Postfix) is already installed")
                        Log.info(
                            self, "Another mta (Postfix) is already installed")

            # proftpd
            if pargs.proftpd:
                Log.debug(self, "Setting apt_packages variable for ProFTPd")
                if not KCAptGet.is_installed(self, 'proftpd-basic'):
                    apt_packages = apt_packages + ["proftpd-basic"]
                else:
                    Log.debug(self, "ProFTPd already installed")
                    Log.info(self, "ProFTPd already installed")

            # PHPMYADMIN
            if pargs.phpmyadmin:
                pargs.composer = True
                if not os.path.isdir('/var/www/22222/htdocs/db/pma'):
                    Log.debug(self, "Setting packages variable "
                              "for phpMyAdmin ")
                    packages = packages + [[
                        "https://www.phpmyadmin.net/"
                        "downloads/phpMyAdmin-latest-all-languages.tar.gz",
                        "/var/lib/kc/tmp/pma.tar.gz",
                        "PHPMyAdmin"]]
                else:
                    Log.debug(self, "phpMyAdmin already installed")
                    Log.info(self, "phpMyAdmin already installed")

            # PHPREDISADMIN
            if pargs.phpredisadmin:
                pargs.composer = True
                if not os.path.isdir('/var/www/22222/htdocs/'
                                     'cache/redis/phpRedisAdmin'):
                    Log.debug(
                        self, "Setting packages variable for phpRedisAdmin")
                    packages = packages + [["https://github.com/"
                                            "erikdubbelboer/"
                                            "phpRedisAdmin/archive"
                                            "/v1.11.3.tar.gz",
                                            "/var/lib/kc/tmp/pra.tar.gz",
                                            "phpRedisAdmin"]]
                else:
                    Log.debug(self, "phpRedisAdmin already installed")
                    Log.info(self, "phpRedisAdmin already installed")

            # Composer
            if pargs.composer:
                if not KCAptGet.is_exec(self, 'php'):
                    pargs.php = True
                if not KCAptGet.is_exec(self, 'composer'):
                    Log.debug(self, "Setting packages variable for Composer ")
                    packages = packages + [["https://getcomposer.org/"
                                            "installer",
                                            "/var/lib/kc/tmp/composer-install",
                                            "Composer"]]
                else:
                    Log.debug(self, "Composer already installed")
                    Log.info(self, "Composer already installed")

            # ADMINER
            if pargs.adminer:
                if not os.path.isfile("{0}22222/htdocs/db/"
                                      "adminer/index.php"
                                      .format(KCVar.kc_webroot)):
                    Log.debug(self, "Setting packages variable for Adminer ")
                    packages = packages + [[
                        "https://www.adminer.org/latest.php",
                        "{0}22222/"
                        "htdocs/db/adminer/index.php"
                        .format(KCVar.kc_webroot),
                        "Adminer"],
                        ["https://raw.githubusercontent.com"
                         "/vrana/adminer/master/designs/"
                         "pepa-linha/adminer.css",
                         "{0}22222/"
                         "htdocs/db/adminer/adminer.css"
                         .format(KCVar.kc_webroot),
                         "Adminer theme"]]
                else:
                    Log.debug(self, "Adminer already installed")
                    Log.info(self, "Adminer already installed")

            # mysqltuner
            if pargs.mysqltuner:
                if not os.path.isfile("/usr/bin/mysqltuner"):
                    Log.debug(self, "Setting packages variable "
                              "for MySQLTuner ")
                    packages = packages + [["https://raw."
                                            "githubusercontent.com/"
                                            "major/MySQLTuner-perl"
                                            "/master/mysqltuner.pl",
                                            "/usr/bin/mysqltuner",
                                            "MySQLTuner"]]
                else:
                    Log.debug(self, "MySQLtuner already installed")
                    Log.info(self, "MySQLtuner already installed")

            # Netdata
            if pargs.netdata:
                if (not os.path.isdir('/opt/netdata') and not
                        os.path.isdir("/etc/netdata")):
                    Log.debug(
                        self, "Setting packages variable for Netdata")
                    packages = packages + [['https://my-netdata.io/'
                                            'kickstart.sh',
                                            '/var/lib/kc/tmp/kickstart.sh',
                                            'Netdata']]
                else:
                    Log.debug(self, "Netdata already installed")
                    Log.info(self, "Netdata already installed")

            # KeepCloud Dashboard
            if pargs.dashboard:
                if not os.path.isfile('/var/www/22222/htdocs/index.php'):
                    Log.debug(self,
                              "Setting packages variable for KC-Dashboard")
                    packages = packages + [[
                        "https://github.com/KeepCloud"
                        "/kc-dashboard/"
                        "releases/download/v{0}/"
                        "kc-dashboard.tar.gz"
                        .format(KCVar.kc_dashboard),
                        "/var/lib/kc/tmp/kc-dashboard.tar.gz",
                        "KeepCloud Dashboard"]]
                else:
                    Log.debug(self, "KeepCloud dashboard already installed")
                    Log.info(self, "KeepCloud dashboard already installed")

            # eXtplorer
            if pargs.extplorer:
                if not os.path.isdir('/var/www/22222/htdocs/files'):
                    Log.debug(self, "Setting packages variable for eXtplorer")
                    packages = packages + \
                        [["https://github.com/soerennb/"
                          "extplorer/archive/v{0}.tar.gz"
                          .format(KCVar.kc_extplorer),
                          "/var/lib/kc/tmp/extplorer.tar.gz",
                          "eXtplorer"]]
                else:
                    Log.debug(self, "eXtplorer is already installed")
                    Log.info(self, "eXtplorer is already installed")

            # ultimate ngx_blocker
            if pargs.ngxblocker:
                if not KCAptGet.is_exec(self, 'nginx'):
                    pargs.nginx = True
                if not os.path.isdir('/etc/nginx/bots.d'):
                    Log.debug(self, "Setting packages variable for ngxblocker")
                    packages = packages + \
                        [["https://raw.githubusercontent.com/"
                          "mitchellkrogza/nginx-ultimate-bad-bot-blocker"
                          "/master/install-ngxblocker",
                          "/usr/local/sbin/install-ngxblocker",
                          "ngxblocker"]]
                else:
                    Log.debug(self, "ngxblocker is already installed")
                    Log.info(self, "ngxblocker is already installed")

            # cheat.sh
            if pargs.cheat:
                if ((not os.path.exists('/usr/local/bin/cht.sh')) and
                        (not os.path.exists('/usr/bin/cht.sh'))):
                    Log.debug(self, 'Setting packages variable for cheat.sh')
                    packages = packages + [[
                        "https://raw.githubusercontent.com/chubin/cheat.sh"
                        "/master/share/cht.sh.txt",
                        "/usr/local/bin/cht.sh",
                        "cheat.sh"],
                        ["https://raw.githubusercontent.com/chubin/cheat.sh"
                         "/master/share/bash_completion.txt",
                         "/etc/bash_completion.d/cht.sh",
                         "bash_completion"]]

            if pargs.nanorc:
                if not os.path.exists('/usr/share/nano-syntax-highlighting'):
                    Log.debug(self, "Setting packages variable for nanorc")
                    apt_packages = apt_packages + ['nano']

            # UTILS
            if pargs.utils:
                if not KCShellExec.cmd_exec(self, 'mysqladmin ping'):
                    pargs.mysql = True
                if not (KCAptGet.is_installed(self, 'php7.2-fpm') or
                        KCAptGet.is_installed(self, 'php7.3-fpm') or
                        KCAptGet.is_installed(self, 'php7.4-fpm') or
                        KCAptGet.is_installed(self, 'php8.0-fpm') or
                        KCAptGet.is_installed(self, 'php8.1-fpm')):
                    pargs.php80 = True
                Log.debug(self, "Setting packages variable for utils")
                packages = packages + [[
                    "https://raw.githubusercontent.com"
                    "/rtCamp/eeadmin/master/cache/nginx/"
                    "clean.php",
                    "{0}22222/htdocs/cache/nginx/clean.php"
                    .format(KCVar.kc_webroot),
                    "clean.php"],
                    ["https://raw.github.com/rlerdorf/"
                     "opcache-status/master/opcache.php",
                     "{0}22222/htdocs/cache/opcache/opcache.php"
                     .format(KCVar.kc_webroot),
                     "opcache.php"],
                    ["https://raw.github.com/amnuts/"
                     "opcache-gui/master/index.php",
                     "{0}22222/htdocs/cache/opcache/opgui.php"
                     .format(KCVar.kc_webroot),
                     "Opgui"],
                    ["https://raw.githubusercontent.com/"
                     "mlazarov/ocp/master/ocp.php",
                     "{0}22222/htdocs/cache/opcache/ocp.php"
                     .format(KCVar.kc_webroot),
                     "OCP.php"],
                    ["https://github.com/jokkedk/webgrind/"
                     "archive/master.tar.gz",
                     '/var/lib/kc/tmp/webgrind.tar.gz',
                     'Webgrind'],
                    ["https://www.percona.com/"
                     "get/pt-query-digest",
                     "/usr/bin/pt-query-advisor",
                     "pt-query-advisor"],
                    ["https://github.com/box/Anemometer/"
                     "archive/master.tar.gz",
                     '/var/lib/kc/tmp/anemometer.tar.gz',
                     'Anemometer']]

        except Exception as e:
            Log.debug(self, "{0}".format(e))

        if (apt_packages) or (packages):
            pre_stack(self)
            if (apt_packages):
                Log.debug(self, "Calling pre_pref")
                pre_pref(self, apt_packages)
                # meminfo = (os.popen('/bin/cat /proc/meminfo '
                #                    '| grep MemTotal').read()).split(":")
                # memsplit = re.split(" kB", meminfo[1])
                # kc_mem = int(memsplit[0])
                # if (kc_mem < 4000000):
                #    KCSwap.add(self)
                Log.wait(self, "Updating apt-cache          ")
                KCAptGet.update(self)
                Log.valide(self, "Updating apt-cache          ")
                Log.wait(self, "Installing APT packages     ")
                KCAptGet.install(self, apt_packages)
                Log.valide(self, "Installing APT packages     ")
                post_pref(self, apt_packages, [])
            if (packages):
                Log.debug(self, "Downloading following: {0}".format(packages))
                KCDownload.download(self, packages)
                Log.debug(self, "Calling post_pref")
                Log.wait(self, "Configuring packages")
                post_pref(self, [], packages)
                Log.valide(self, "Configuring packages")

            if disp_msg:
                if (self.msg):
                    for msg in self.msg:
                        Log.info(self, Log.ENDC + msg)
                Log.info(self, "Successfully installed packages")
            else:
                return self.msg
        return 0

    @expose(help="Remove packages")
    def remove(self):
        """Start removal of packages"""
        apt_packages = []
        packages = []
        pargs = self.app.pargs
        if ((not pargs.web) and (not pargs.admin) and
            (not pargs.nginx) and (not pargs.php) and
            (not pargs.mysql) and (not pargs.wpcli) and
            (not pargs.mariadb) and
            (not pargs.phpmyadmin) and (not pargs.composer) and
                (not pargs.netdata) and (not pargs.dashboard) and
                (not pargs.fail2ban) and (not pargs.security) and
                (not pargs.mysqlclient) and (not pargs.mysqltuner) and
                (not pargs.adminer) and (not pargs.utils) and
                (not pargs.redis) and (not pargs.proftpd) and
                (not pargs.extplorer) and (not pargs.clamav) and
                (not pargs.cheat) and (not pargs.nanorc) and
                (not pargs.ufw) and (not pargs.ngxblocker) and
                (not pargs.phpredisadmin) and (not pargs.sendmail) and
                (not pargs.php73) and (not pargs.php74) and
                (not pargs.php72) and (not pargs.php80) and
                (not pargs.php81) and (not pargs.all)):
            self.app.args.print_help()

        if pargs.php:
            pargs.php72 = True

        if pargs.mariadb:
            pargs.mysql = True

        if pargs.all:
            pargs.web = True
            pargs.admin = True
            pargs.php73 = True
            pargs.php74 = True
            pargs.fail2ban = True
            pargs.proftpd = True
            pargs.utils = True
            pargs.redis = True
            pargs.security = True
            pargs.nanorc = True
            packages = packages + ['/var/www/22222/htdocs']

        if pargs.web:
            pargs.nginx = True
            pargs.php73 = True
            pargs.mysql = True
            pargs.wpcli = True
            pargs.sendmail = True

        if pargs.admin:
            pargs.composer = True
            pargs.utils = True
            pargs.netdata = True
            pargs.mysqltuner = True
            pargs.cheat = True

        if pargs.security:
            pargs.fail2ban = True
            pargs.clamav = True
            pargs.ufw = True
            pargs.ngxblocker = True

        # NGINX
        if pargs.nginx:
            if KCAptGet.is_installed(self, 'nginx-custom'):
                Log.debug(self, "Removing apt_packages variable of Nginx")
                apt_packages = apt_packages + KCVar.kc_nginx

        # PHP 7.2
        if pargs.php72:
            Log.debug(self, "Setting apt_packages variable for PHP 7.2")
            if (KCAptGet.is_installed(self, 'php7.2-fpm')):
                apt_packages = apt_packages + KCVar.kc_php72
                if not (KCAptGet.is_installed(self, 'php7.3-fpm') or
                        KCAptGet.is_installed(self, 'php7.4-fpm') or
                        KCAptGet.is_installed(self, 'php8.0-fpm') or
                        KCAptGet.is_installed(self, 'php8.1-fpm')):
                    apt_packages = apt_packages + KCVar.kc_php_extra
            else:
                Log.debug(self, "PHP 7.2 is not installed")
                Log.info(self, "PHP 7.2 is not installed")

        # PHP 7.3
        if pargs.php73:
            Log.debug(self, "Setting apt_packages variable for PHP 7.3")
            if KCAptGet.is_installed(self, 'php7.3-fpm'):
                apt_packages = apt_packages + KCVar.kc_php73
                if not (KCAptGet.is_installed(self, 'php7.2-fpm') or
                        KCAptGet.is_installed(self, 'php7.4-fpm') or
                        KCAptGet.is_installed(self, 'php8.0-fpm') or
                        KCAptGet.is_installed(self, 'php8.1-fpm')):
                    apt_packages = apt_packages + KCVar.kc_php_extra
            else:
                Log.debug(self, "PHP 7.3 is not installed")
                Log.info(self, "PHP 7.3 is not installed")

        # PHP 7.4
        if pargs.php74:
            Log.debug(self, "Setting apt_packages variable for PHP 7.4")
            if KCAptGet.is_installed(self, 'php7.4-fpm'):
                apt_packages = apt_packages + KCVar.kc_php74
                if not (KCAptGet.is_installed(self, 'php7.3-fpm') or
                        KCAptGet.is_installed(self, 'php7.2-fpm') or
                        KCAptGet.is_installed(self, 'php8.0-fpm') or
                        KCAptGet.is_installed(self, 'php8.1-fpm')):
                    apt_packages = apt_packages + KCVar.kc_php_extra
            else:
                Log.debug(self, "PHP 7.4 is not installed")
                Log.info(self, "PHP 7.4 is not installed")

        # PHP 8.0
        if pargs.php80:
            Log.debug(self, "Setting apt_packages variable for PHP 8.0")
            if KCAptGet.is_installed(self, 'php8.0-fpm'):
                apt_packages = apt_packages + KCVar.kc_php80
                if not (KCAptGet.is_installed(self, 'php7.3-fpm') or
                        KCAptGet.is_installed(self, 'php7.2-fpm') or
                        KCAptGet.is_installed(self, 'php7.4-fpm') or
                        KCAptGet.is_installed(self, 'php8.1-fpm')):
                    apt_packages = apt_packages + KCVar.kc_php_extra
            else:
                Log.debug(self, "PHP 8.0 is not installed")
                Log.info(self, "PHP 8.0 is not installed")

        # PHP 8.1
        if pargs.php81:
            Log.debug(self, "Setting apt_packages variable for PHP 8.1")
            if KCAptGet.is_installed(self, 'php8.1-fpm'):
                apt_packages = apt_packages + KCVar.kc_php81
                if not (KCAptGet.is_installed(self, 'php7.3-fpm') or
                        KCAptGet.is_installed(self, 'php7.2-fpm') or
                        KCAptGet.is_installed(self, 'php7.4-fpm') or
                        KCAptGet.is_installed(self, 'php8.0-fpm')):
                    apt_packages = apt_packages + KCVar.kc_php_extra
            else:
                Log.debug(self, "PHP 8.1 is not installed")
                Log.info(self, "PHP 8.1 is not installed")

        # REDIS
        if pargs.redis:
            if KCAptGet.is_installed(self, 'redis-server'):
                Log.debug(self, "Remove apt_packages variable of Redis")
                apt_packages = apt_packages + ["redis-server"]

        # MariaDB
        if pargs.mysql:
            if KCAptGet.is_installed(self, 'mariadb-server'):
                Log.debug(self, "Removing apt_packages variable of MySQL")
                apt_packages = apt_packages + KCVar.kc_mysql

        # mysqlclient
        if pargs.mysqlclient:
            Log.debug(self, "Removing apt_packages variable "
                      "for MySQL Client")
            if KCShellExec.cmd_exec(self, "mysqladmin ping"):
                apt_packages = apt_packages + KCVar.kc_mysql_client

        # fail2ban
        if pargs.fail2ban:
            if KCAptGet.is_installed(self, 'fail2ban'):
                Log.debug(self, "Remove apt_packages variable of Fail2ban")
                apt_packages = apt_packages + KCVar.kc_fail2ban

        # ClamAV
        if pargs.clamav:
            Log.debug(self, "Setting apt_packages variable for ClamAV")
            if KCAptGet.is_installed(self, 'clamav'):
                apt_packages = apt_packages + KCVar.kc_clamav

        # sendmail
        if pargs.sendmail:
            Log.debug(self, "Setting apt_packages variable for Sendmail")
            if KCAptGet.is_installed(self, 'sendmail'):
                apt_packages = apt_packages + ["sendmail"]

        # proftpd
        if pargs.proftpd:
            if KCAptGet.is_installed(self, 'proftpd-basic'):
                Log.debug(self, "Remove apt_packages variable for ProFTPd")
                apt_packages = apt_packages + ["proftpd-basic"]

        # UFW
        if pargs.ufw:
            if KCAptGet.is_installed(self, 'ufw'):
                Log.debug(self, "Remove apt_packages variable for UFW")
                KCShellExec.cmd_exec(self, 'ufw disable && ufw --force reset')

        # nanorc
        if pargs.nanorc:
            if os.path.exists('/usr/share/nano-syntax-highlighting'):
                Log.debug(self, "Add nano to apt_packages list")
                packages = packages + \
                    ["/usr/share/nano-syntax-highlighting"]

        # WPCLI
        if pargs.wpcli:
            Log.debug(self, "Removing package variable of WPCLI ")
            if os.path.isfile('/usr/local/bin/wp'):
                packages = packages + ['/usr/local/bin/wp']

        # PHPMYADMIN
        if pargs.phpmyadmin:
            if os.path.isdir('{0}22222/htdocs/db/pma'
                             .format(KCVar.kc_webroot)):
                Log.debug(self, "Removing package of phpMyAdmin ")
                packages = packages + ['{0}22222/htdocs/db/pma'
                                       .format(KCVar.kc_webroot)]
        # Composer
        if pargs.composer:
            Log.debug(self, "Removing package of Composer ")
            if os.path.isfile('/usr/local/bin/composer'):
                packages = packages + ['/usr/local/bin/composer']

        # MySQLTuner
        if pargs.mysqltuner:
            if os.path.isfile('/usr/bin/mysqltuner'):
                Log.debug(self, "Removing packages for MySQLTuner ")
                packages = packages + ['/usr/bin/mysqltuner']

        # cheat.sh
        if pargs.cheat:
            if os.path.isfile('/usr/local/bin/cht.sh'):
                Log.debug(self, "Removing packages for cheat.sh ")
                packages = packages + [
                    '/usr/local/bin/cht.sh', '/usr/local/bin/cheat',
                    '/etc/bash_completion.d/cht.sh']

        # PHPREDISADMIN
        if pargs.phpredisadmin:
            Log.debug(self, "Removing package variable of phpRedisAdmin ")
            if os.path.isdir('{0}22222/htdocs/cache/redis'
                             .format(KCVar.kc_webroot)):
                packages = packages + ['{0}22222/htdocs/'
                                       'cache/redis'
                                       .format(KCVar.kc_webroot)]
        # ADMINER
        if pargs.adminer:
            if os.path.isdir('{0}22222/htdocs/db/adminer'
                             .format(KCVar.kc_webroot)):
                Log.debug(self, "Removing package variable of Adminer ")
                packages = packages + ['{0}22222/htdocs/db/adminer'
                                       .format(KCVar.kc_webroot)]
        if pargs.utils:
            Log.debug(self, "Removing package variable of utils ")
            packages = packages + ['{0}22222/htdocs/php/webgrind/'
                                   .format(KCVar.kc_webroot),
                                   '{0}22222/htdocs/cache/opcache'
                                   .format(KCVar.kc_webroot),
                                   '{0}22222/htdocs/cache/nginx/'
                                   'clean.php'.format(KCVar.kc_webroot),
                                   '/usr/bin/pt-query-advisor',
                                   '{0}22222/htdocs/db/anemometer'
                                   .format(KCVar.kc_webroot)]

        # netdata
        if pargs.netdata:
            if (os.path.exists('/opt/netdata') or
                    os.path.exists('/etc/netdata')):
                Log.debug(self, "Removing Netdata")
                packages = packages + ['/var/lib/kc/tmp/kickstart.sh']

        # KeepCloud dashboard
        if pargs.dashboard:
            if (os.path.isfile('{0}22222/htdocs/index.php'
                               .format(KCVar.kc_webroot)) or
                    os.path.isfile('{0}22222/htdocs/index.html'
                                   .format(KCVar.kc_webroot))):
                Log.debug(self, "Removing kc-Dashboard")
                packages = packages + ['{0}22222/htdocs/assets'
                                       .format(KCVar.kc_webroot),
                                       '{0}22222/htdocs/index.php'
                                       .format(KCVar.kc_webroot),
                                       '{0}22222/htdocs/index.html'
                                       .format(KCVar.kc_webroot)]
        # ngxblocker
        if pargs.ngxblocker:
            if os.path.isfile('/usr/local/sbin/setup-ngxblocker'):
                packages = packages + [
                    '/usr/local/sbin/setup-ngxblocker',
                    '/usr/local/sbin/install-ngxblocker',
                    '/usr/local/sbin/update-ngxblocker',
                    '/etc/nginx/conf.d/globalblacklist.conf',
                    '/etc/nginx/conf.d/botblocker-nginx-settings.conf',
                    '/etc/nginx/bots.d']

        if (packages) or (apt_packages):
            if (not pargs.force):
                start_remove = input('Are you sure you to want to'
                                     ' remove from server.'
                                     '\nPackage configuration will remain'
                                     ' on server after this operation.\n'
                                     'Remove stacks [y/N]?')
                if start_remove != "Y" and start_remove != "y":
                    Log.error(self, "Not starting stack removal")

            if 'nginx-custom' in apt_packages:
                KCService.stop_service(self, 'nginx')

            if 'mariadb-server' in apt_packages:
                KCMysql.backupAll(self)
                KCService.stop_service(self, 'mysql')

            # Netdata uninstaller
            if '/var/lib/kc/tmp/kickstart.sh' in packages:
                if os.path.exists(
                        '/usr/libexec/netdata/netdata-uninstaller.sh'):
                    Log.debug(self, "Uninstalling Netdata from /etc/netdata")
                    KCShellExec.cmd_exec(
                        self, "bash /usr/libexec/netdata/netdata-"
                        "uninstaller.sh -y -f",
                        errormsg='', log=False)
                    packages = packages + ["/etc/netdata"]
                elif os.path.exists(
                    '/opt/netdata/usr/libexec/'
                        'netdata/netdata-uninstaller.sh'):
                    Log.debug(self, "Uninstalling Netdata from /opt/netdata")
                    KCShellExec.cmd_exec(
                        self, "bash /opt/netdata/usr/libexec/netdata/netdata-"
                        "uninstaller.sh -y -f")
                    packages = packages + ["/opt/netdata"]
                else:
                    Log.debug(self, "Netdata uninstaller not found")
                if KCShellExec.cmd_exec(self, 'mysqladmin ping'):
                    KCMysql.execute(
                        self, "DELETE FROM mysql.user WHERE User = 'netdata';")

            if (packages):
                Log.wait(self, "Removing packages           ")
                KCFileUtils.remove(self, packages)
                Log.valide(self, "Removing packages           ")

                if '/usr/share/nano-syntax-highlighting' in packages:
                    # removing include line from nanorc
                    KCShellExec.cmd_exec(
                        self, 'grep -v "nano-syntax-highlighting" '
                        '/etc/nanorc > /etc/nanorc.new')
                    KCFileUtils.rm(self, '/etc/nanorc')
                    KCFileUtils.mvfile(
                        self, '/etc/nanorc.new', '/etc/nanorc')

            if (apt_packages):
                Log.debug(self, "Removing apt_packages")
                Log.wait(self, "Removing APT packages       ")
                KCAptGet.remove(self, apt_packages)
                KCAptGet.auto_remove(self)
                Log.valide(self, "Removing APT packages       ")

            Log.info(self, "Successfully removed packages")

    @expose(help="Purge packages")
    def purge(self):
        """Start purging of packages"""
        apt_packages = []
        packages = []
        pargs = self.app.pargs
        # Default action for stack purge
        if ((not pargs.web) and (not pargs.admin) and
            (not pargs.nginx) and (not pargs.php) and
            (not pargs.mysql) and (not pargs.wpcli) and
            (not pargs.mariadb) and
            (not pargs.phpmyadmin) and (not pargs.composer) and
                (not pargs.netdata) and (not pargs.dashboard) and
                (not pargs.fail2ban) and (not pargs.security) and
                (not pargs.mysqlclient) and (not pargs.mysqltuner) and
                (not pargs.adminer) and (not pargs.utils) and
                (not pargs.redis) and (not pargs.proftpd) and
                (not pargs.extplorer) and (not pargs.clamav) and
                (not pargs.cheat) and (not pargs.nanorc) and
                (not pargs.ufw) and (not pargs.ngxblocker) and
                (not pargs.phpredisadmin) and (not pargs.sendmail) and
                (not pargs.php80) and (not pargs.php81) and
                (not pargs.php73) and (not pargs.php74) and
                (not pargs.php72) and (not pargs.all)):
            self.app.args.print_help()

        if pargs.php:
            pargs.php72 = True

        if pargs.mariadb:
            pargs.mysql = True

        if pargs.all:
            pargs.web = True
            pargs.admin = True
            pargs.php73 = True
            pargs.php74 = True
            pargs.php80 = True
            pargs.php81 = True
            pargs.fail2ban = True
            pargs.proftpd = True
            pargs.utils = True
            pargs.redis = True
            packages = packages + ['/var/www/22222/htdocs']

        if pargs.web:
            pargs.nginx = True
            pargs.php73 = True
            pargs.mysql = True
            pargs.wpcli = True
            pargs.sendmail = True

        if pargs.admin:
            pargs.utils = True
            pargs.composer = True
            pargs.netdata = True
            pargs.mysqltuner = True
            pargs.cheat = True
            packages = packages + ['/var/www/22222/htdocs']

        if pargs.security:
            pargs.fail2ban = True
            pargs.clamav = True
            pargs.ufw = True
            pargs.ngxblocker = True

        # NGINX
        if pargs.nginx:
            if KCAptGet.is_installed(self, 'nginx-custom'):
                Log.debug(self, "Add Nginx to apt_packages list")
                apt_packages = apt_packages + KCVar.kc_nginx
            else:
                Log.info(self, "Nginx is not installed")

        # PHP 7.2
        if pargs.php72:
            Log.debug(self, "Setting apt_packages variable for PHP 7.2")
            if (KCAptGet.is_installed(self, 'php7.2-fpm')):
                apt_packages = apt_packages + KCVar.kc_php72
                if not (KCAptGet.is_installed(self, 'php7.3-fpm') or
                        KCAptGet.is_installed(self, 'php7.4-fpm')):
                    apt_packages = apt_packages + KCVar.kc_php_extra
            else:
                Log.debug(self, "PHP 7.2 is not installed")
                Log.info(self, "PHP 7.2 is not installed")

        # PHP 7.3
        if pargs.php73:
            Log.debug(self, "Setting apt_packages variable for PHP 7.3")
            if KCAptGet.is_installed(self, 'php7.3-fpm'):
                apt_packages = apt_packages + KCVar.kc_php73
                if not (KCAptGet.is_installed(self, 'php7.2-fpm') or
                        KCAptGet.is_installed(self, 'php7.4-fpm') or
                        KCAptGet.is_installed(self, 'php8.0-fpm') or
                        KCAptGet.is_installed(self, 'php8.1-fpm')):
                    apt_packages = apt_packages + KCVar.kc_php_extra
            else:
                Log.debug(self, "PHP 7.3 is not installed")
                Log.info(self, "PHP 7.3 is not installed")

        # PHP 7.4
        if pargs.php74:
            Log.debug(self, "Setting apt_packages variable for PHP 7.4")
            if KCAptGet.is_installed(self, 'php7.4-fpm'):
                apt_packages = apt_packages + KCVar.kc_php74
                if not (KCAptGet.is_installed(self, 'php7.3-fpm') or
                        KCAptGet.is_installed(self, 'php7.2-fpm') or
                        KCAptGet.is_installed(self, 'php8.0-fpm') or
                        KCAptGet.is_installed(self, 'php8.1-fpm')):
                    apt_packages = apt_packages + KCVar.kc_php_extra
            else:
                Log.debug(self, "PHP 7.4 is not installed")
                Log.info(self, "PHP 7.4 is not installed")

        # PHP 8.0
        if pargs.php80:
            Log.debug(self, "Setting apt_packages variable for PHP 8.0")
            if KCAptGet.is_installed(self, 'php8.0-fpm'):
                apt_packages = apt_packages + KCVar.kc_php80
                if not (KCAptGet.is_installed(self, 'php7.3-fpm') or
                        KCAptGet.is_installed(self, 'php7.2-fpm') or
                        KCAptGet.is_installed(self, 'php7.4-fpm') or
                        KCAptGet.is_installed(self, 'php8.1-fpm')):
                    apt_packages = apt_packages + KCVar.kc_php_extra
            else:
                Log.debug(self, "PHP 8.0 is not installed")
                Log.info(self, "PHP 8.0 is not installed")

        # PHP 8.1
        if pargs.php81:
            Log.debug(self, "Setting apt_packages variable for PHP 8.1")
            if KCAptGet.is_installed(self, 'php8.1-fpm'):
                apt_packages = apt_packages + KCVar.kc_php74
                if not (KCAptGet.is_installed(self, 'php7.3-fpm') or
                        KCAptGet.is_installed(self, 'php7.2-fpm') or
                        KCAptGet.is_installed(self, 'php8.0-fpm') or
                        KCAptGet.is_installed(self, 'php7.4-fpm')):
                    apt_packages = apt_packages + KCVar.Kc_php_extra
            else:
                Log.debug(self, "PHP 8.1 is not installed")
                Log.info(self, "PHP 8.1 is not installed")

        # REDIS
        if pargs.redis:
            if KCAptGet.is_installed(self, 'redis-server'):
                Log.debug(self, "Remove apt_packages variable of Redis")
                apt_packages = apt_packages + ["redis-server"]
            else:
                Log.info(self, "Redis is not installed")

        # MariaDB
        if pargs.mysql:
            if KCAptGet.is_installed(self, 'mariadb-server'):
                Log.debug(self, "Add MySQL to apt_packages list")
                apt_packages = apt_packages + ['mariadb-server',
                                               'mysql-common',
                                               'mariadb-client']
                packages = packages + ['/etc/mysql', '/var/lib/mysql']
            else:
                Log.info(self, "MariaDB is not installed")

        # mysqlclient
        if pargs.mysqlclient:
            if KCShellExec.cmd_exec(self, "mysqladmin ping"):
                Log.debug(self, "Add MySQL client to apt_packages list")
                apt_packages = apt_packages + KCVar.kc_mysql_client

        # fail2ban
        if pargs.fail2ban:
            if KCAptGet.is_installed(self, 'fail2ban'):
                Log.debug(self, "Add Fail2ban to apt_packages list")
                apt_packages = apt_packages + KCVar.kc_fail2ban

        # ClamAV
        if pargs.clamav:
            if KCAptGet.is_installed(self, 'clamav'):
                Log.debug(self, "Add ClamAV to apt_packages list")
                apt_packages = apt_packages + KCVar.kc_clamav

        # UFW
        if pargs.ufw:
            if KCAptGet.is_installed(self, 'ufw'):
                Log.debug(self, "Add UFW to apt_packages list")
                KCShellExec.cmd_exec(self, 'ufw disable && ufw --force reset')

        # sendmail
        if pargs.sendmail:
            if KCAptGet.is_installed(self, 'sendmail'):
                Log.debug(self, "Add sendmail to apt_packages list")
                apt_packages = apt_packages + ["sendmail"]

        # proftpd
        if pargs.proftpd:
            if KCAptGet.is_installed(self, 'proftpd-basic'):
                Log.debug(self, "Add Proftpd to apt_packages list")
                apt_packages = apt_packages + ["proftpd-basic"]

        # nanorc
        if pargs.nanorc:
            if os.path.exists('/usr/share/nano-syntax-highlighting'):
                Log.debug(self, "Add nano to apt_packages list")
                packages = packages + \
                    ["/usr/share/nano-syntax-highlighting"]

        # WP-CLI
        if pargs.wpcli:
            if os.path.isfile('/usr/local/bin/wp'):
                Log.debug(self, "Purge package variable WPCLI")
                packages = packages + ['/usr/local/bin/wp']

        # PHPMYADMIN
        if pargs.phpmyadmin:
            if os.path.isdir('{0}22222/htdocs/db/pma'
                             .format(KCVar.kc_webroot)):
                Log.debug(self, "Removing package of phpMyAdmin ")
                packages = packages + ['{0}22222/htdocs/db/pma'
                                       .format(KCVar.kc_webroot)]

        # Composer
        if pargs.composer:
            if os.path.isfile('/usr/local/bin/composer'):
                Log.debug(self, "Removing package variable of Composer ")
                packages = packages + ['/usr/local/bin/composer']

        # MySQLTuner
        if pargs.mysqltuner:
            if os.path.isfile('/usr/bin/mysqltuner'):
                Log.debug(self, "Removing packages for MySQLTuner ")
                packages = packages + ['/usr/bin/mysqltuner']

        # cheat.sh
        if pargs.cheat:
            if os.path.isfile('/usr/local/bin/cht.sh'):
                Log.debug(self, "Removing packages for cheat.sh ")
                packages = packages + [
                    '/usr/local/bin/cht.sh', '/usr/local/bin/cheat',
                    '/etc/bash_completion.d/cht.sh']

        # PHPREDISADMIN
        if pargs.phpredisadmin:
            Log.debug(self, "Removing package variable of phpRedisAdmin ")
            if os.path.isdir('{0}22222/htdocs/cache/redis'
                             .format(KCVar.kc_webroot)):
                packages = packages + ['{0}22222/htdocs/'
                                       'cache/redis'
                                       .format(KCVar.kc_webroot)]
        # ADMINER
        if pargs.adminer:
            if os.path.isdir('{0}22222/htdocs/db/adminer'
                             .format(KCVar.kc_webroot)):
                Log.debug(self, "Removing package variable of Adminer ")
                packages = packages + ['{0}22222/htdocs/db/adminer'
                                       .format(KCVar.kc_webroot)]
        # utils
        if pargs.utils:
            Log.debug(self, "Purge package variable utils")
            packages = packages + ['{0}22222/htdocs/php/webgrind/'
                                   .format(KCVar.kc_webroot),
                                   '{0}22222/htdocs/cache/opcache'
                                   .format(KCVar.kc_webroot),
                                   '{0}22222/htdocs/cache/nginx/'
                                   'clean.php'.format(KCVar.kc_webroot),
                                   '/usr/bin/pt-query-advisor',
                                   '{0}22222/htdocs/db/anemometer'
                                   .format(KCVar.kc_webroot)
                                   ]
        # netdata
        if pargs.netdata:
            if (os.path.exists('/opt/netdata') or
                    os.path.exists('/etc/netdata')):
                Log.debug(self, "Removing Netdata")
                packages = packages + ['/var/lib/kc/tmp/kickstart.sh']

        # KeepCloud dashboard
        if pargs.dashboard:
            Log.debug(self, "Removing kc-Dashboard")
            packages = packages + ['{0}22222/htdocs/assets/'
                                   .format(KCVar.kc_webroot),
                                   '{0}22222/htdocs/index.php'
                                   .format(KCVar.kc_webroot)]

        # ngxblocker
        if pargs.ngxblocker:
            if os.path.isfile('/usr/local/sbin/setup-ngxblocker'):
                packages = packages + [
                    '/usr/local/sbin/setup-ngxblocker',
                    '/usr/local/sbin/install-ngxblocker',
                    '/usr/local/sbin/update-ngxblocker',
                    '/etc/nginx/conf.d/globalblacklist.conf',
                    '/etc/nginx/conf.d/botblocker-nginx-settings.conf',
                    '/etc/nginx/bots.d']

        if (packages) or (apt_packages):
            if (not pargs.force):
                start_purge = input('Are you sure you to want to'
                                    ' purge stacks from this server ?'
                                    '\nPackage configuration and data '
                                    'will not remain'
                                    ' on this server after this operation.\n'
                                    'Purge stacks [y/N]')
                if start_purge != "Y" and start_purge != "y":
                    Log.error(self, "Not starting stack purge")

            if "nginx-custom" in apt_packages:
                KCService.stop_service(self, 'nginx')

            if "fail2ban" in apt_packages:
                KCService.stop_service(self, 'fail2ban')

            if "mariadb-server" in apt_packages:
                if self.app.config.has_section('mysql'):
                    if self.app.config.get(
                            'mysql', 'grant-host') == 'localhost':
                        KCMysql.backupAll(self)
                KCService.stop_service(self, 'mysql')

            # Netdata uninstaller
            if '/var/lib/kc/tmp/kickstart.sh' in packages:
                if os.path.exists(
                        '/usr/libexec/netdata/netdata-uninstaller.sh'):
                    Log.debug(self, "Uninstalling Netdata from /etc/netdata")
                    KCShellExec.cmd_exec(
                        self, "bash /usr/libexec/netdata/netdata-"
                        "uninstaller.sh -y -f",
                        errormsg='', log=False)
                    packages = packages + ["/etc/netdata"]
                elif os.path.exists(
                    '/opt/netdata/usr/libexec/'
                        'netdata/netdata-uninstaller.sh'):
                    Log.debug(self, "Uninstalling Netdata from /opt/netdata")
                    KCShellExec.cmd_exec(
                        self, "bash /opt/netdata/usr/libexec/netdata/netdata-"
                        "uninstaller.sh -y -f")
                    packages = packages + ["/opt/netdata"]
                else:
                    Log.debug(self, "Netdata uninstaller not found")
                if KCShellExec.cmd_exec(self, 'mysqladmin ping'):
                    KCMysql.execute(
                        self, "DELETE FROM mysql.user WHERE User = 'netdata';")

            if (apt_packages):
                Log.wait(self, "Purging APT Packages        ")
                KCAptGet.remove(self, apt_packages, purge=True)
                KCAptGet.auto_remove(self)
                Log.valide(self, "Purging APT Packages        ")
            if (packages):
                Log.wait(self, "Purging Packages            ")
                KCFileUtils.remove(self, packages)
                Log.valide(self, "Purging Packages            ")

                if '/usr/share/nano-syntax-highlighting' in packages:
                    # removing include line from nanorc
                    KCShellExec.cmd_exec(
                        self, 'grep -v "nano-syntax-highlighting" '
                        '/etc/nanorc > /etc/nanorc.new')
                    KCFileUtils.rm(self, '/etc/nanorc')
                    KCFileUtils.mvfile(
                        self, '/etc/nanorc.new', '/etc/nanorc')

            Log.info(self, "Successfully purged packages")


def load(app):
    # register the plugin class.. this only happens if the plugin is enabled
    app.handler.register(KCStackController)
    app.handler.register(KCStackStatusController)
    app.handler.register(KCStackMigrateController)
    app.handler.register(KCStackUpgradeController)

    # register a hook (function) to run after arguments are parsed.
    app.hook.register('post_argument_parsing', kc_stack_hook)
