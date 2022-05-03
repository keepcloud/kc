import configparser
import os
import random
import shutil
import string

import psutil
import requests
from kc.core.apt_repo import KCRepo
from kc.core.aptget import KCAptGet
from kc.core.cron import KCCron
from kc.core.extract import KCExtract
from kc.core.fileutils import KCFileUtils
from kc.core.git import KCGit
from kc.core.logging import Log
from kc.core.mysql import KCMysql
from kc.core.nginxhashbucket import hashbucket
from kc.core.services import KCService
from kc.core.shellexec import CommandExecutionError, KCShellExec
from kc.core.sslutils import SSL
from kc.core.template import KCTemplate
from kc.core.variables import KCVar
from kc.core.stackconf import KCConf
from kc.core.download import KCDownload


def pre_pref(self, apt_packages):
    """Pre settings to do before installation packages"""

    if ("mariadb-server" in apt_packages or "mariadb-client" in apt_packages):
        # add mariadb repository excepted on raspbian and ubuntu 19.04
        if not KCVar.kc_distro == 'raspbian':
            Log.info(self, "Adding repository for MySQL, please wait...")
            mysql_pref = (
                "Package: *\nPin: origin mariadb.mirrors.ovh.net"
                "\nPin-Priority: 1000\n")
            with open('/etc/apt/preferences.d/'
                      'MariaDB.pref', 'w') as mysql_pref_file:
                mysql_pref_file.write(mysql_pref)
            KCRepo.add(self, repo_url=KCVar.kc_mysql_repo)
            KCRepo.add_key(self, '0xcbcb082a1bb943db',
                           keyserver='keyserver.ubuntu.com')
            KCRepo.add_key(self, '0xF1656F24C74CD1D8',
                           keyserver='keyserver.ubuntu.com')
    if ("mariadb-server" in apt_packages and
            not os.path.exists('/etc/mysql/conf.d/my.cnf')):
        # generate random 24 characters root password
        chars = ''.join(random.sample(string.ascii_letters, 24))
        # generate my.cnf root credentials
        mysql_config = """
            [client]
            user = root
            password = {chars}
            socket = /run/mysqld/mysqld.sock
            """.format(chars=chars)
        config = configparser.ConfigParser()
        config.read_string(mysql_config)
        Log.debug(self, 'Writting configuration into MySQL file')
        conf_path = "/etc/mysql/conf.d/my.cnf.tmp"
        os.makedirs(os.path.dirname(conf_path), exist_ok=True)
        with open(conf_path, encoding='utf-8',
                  mode='w') as configfile:
            config.write(configfile)
        Log.debug(self, 'Setting my.cnf permission')
        KCFileUtils.chmod(self, "/etc/mysql/conf.d/my.cnf.tmp", 0o600)

    # add nginx repository
    if set(KCVar.kc_nginx).issubset(set(apt_packages)):
        if (KCVar.kc_distro == 'ubuntu'):
            Log.info(self, "Adding repository for NGINX, please wait...")
            KCRepo.add(self, ppa=KCVar.kc_nginx_repo)
            Log.debug(self, 'Adding ppa for Nginx')
        else:
            if not KCFileUtils.grepcheck(
                    self, '/etc/apt/sources.list/kc-repo.list',
                    'KeepCloud'):
                Log.info(self, "Adding repository for NGINX, please wait...")
                Log.debug(self, 'Adding repository for Nginx')
                KCRepo.add(self, repo_url=KCVar.kc_nginx_repo)
            KCRepo.add_key(self, KCVar.kc_nginx_key)

    # add php repository
    if (('php7.3-fpm' in apt_packages) or
            ('php7.2-fpm' in apt_packages) or ('php7.4-fpm' in apt_packages) or
            ('php8.0-fpm' in apt_packages) or ('php8.1-fpm' in apt_packages)):
        if (KCVar.kc_distro == 'ubuntu'):
            Log.debug(self, 'Adding ppa for PHP')
            Log.info(self, "Adding repository for PHP, please wait...")
            KCRepo.add(self, ppa=KCVar.kc_php_repo)
        else:
            # Add repository for php
            if (KCVar.kc_platform_codename == 'buster'):
                php_pref = ("Package: *\nPin: origin "
                            "packages.sury.org"
                            "\nPin-Priority: 1000\n")
                with open(
                    '/etc/apt/preferences.d/'
                        'PHP.pref', mode='w',
                        encoding='utf-8') as php_pref_file:
                    php_pref_file.write(php_pref)
            if not KCFileUtils.grepcheck(
                    self, '/etc/apt/sources.list.d/kc-repo.list',
                    'packages.sury.org'):
                Log.debug(self, 'Adding repo_url of php for debian')
                Log.info(self, "Adding repository for PHP, please wait...")
                KCRepo.add(self, repo_url=KCVar.kc_php_repo)
            Log.debug(self, 'Adding deb.sury GPG key')
            KCRepo.add_key(self, KCVar.kc_php_key)
    # add redis repository
    if set(KCVar.kc_redis).issubset(set(apt_packages)):
        if KCVar.kc_distro == 'ubuntu':
            Log.info(self, "Adding repository for Redis, please wait...")
            Log.debug(self, 'Adding ppa for redis')
            KCRepo.add(self, ppa=KCVar.kc_redis_repo)
        else:
            if not KCFileUtils.grepcheck(
                    self, '/etc/apt/sources.list/kc-repo.list',
                    'KeepCloud'):
                Log.info(self, "Adding repository for Redis, please wait...")
                KCRepo.add(self, repo_url=KCVar.kc_nginx_repo)
            KCRepo.add_key(self, KCVar.kc_nginx_key)

    # nano
    if 'nano' in apt_packages:
        if KCVar.kc_distro == 'ubuntu':
            if KCVar.kc_platform_codename == 'bionic':
                Log.debug(self, 'Adding ppa for nano')
                KCRepo.add(self, ppa=KCVar.kc_ubuntu_backports)
            elif KCVar.kc_platform_codename == 'xenial':
                Log.debug(self, 'Adding ppa for nano')
                KCRepo.add_key(self, KCVar.kc_nginx_key)
                KCRepo.add(self, repo_url=KCVar.kc_extra_repo)
        else:
            if (not KCFileUtils.grepcheck(
                    self, '/etc/apt/sources.list/kc-repo.list',
                    'KeepCloud')):
                Log.info(self, "Adding repository for Nano, please wait...")
                Log.debug(self, 'Adding repository for Nano')
                KCRepo.add_key(self, KCVar.kc_nginx_key)
                KCRepo.add(self, repo_url=KCVar.kc_nginx_repo)


def post_pref(self, apt_packages, packages, upgrade=False):
    """Post activity after installation of packages"""
    if (apt_packages):
        # Nginx configuration
        if set(KCVar.kc_nginx).issubset(set(apt_packages)):
            Log.info(self, "Applying Nginx configuration templates")
            # Nginx main configuration
            ngxcnf = '/etc/nginx/conf.d'
            ngxcom = '/etc/nginx/common'
            ngxroot = '/var/www/'
            KCGit.add(self, ["/etc/nginx"], msg="Adding Nginx into Git")
            data = dict(tls13=True, release=KCVar.kc_version)
            KCTemplate.deploy(self,
                              '/etc/nginx/nginx.conf',
                              'nginx-core.mustache', data)

            if not os.path.isfile('{0}/gzip.conf.disabled'.format(ngxcnf)):
                data = dict(release=KCVar.kc_version)
                KCTemplate.deploy(self, '{0}/gzip.conf'.format(ngxcnf),
                                  'gzip.mustache', data)

            if not os.path.isfile('{0}/brotli.conf'.format(ngxcnf)):
                KCTemplate.deploy(self,
                                  '{0}/brotli.conf.disabled'
                                  .format(ngxcnf),
                                  'brotli.mustache', data)

            KCTemplate.deploy(self, '{0}/tweaks.conf'.format(ngxcnf),
                              'tweaks.mustache', data)

            # Fix for white screen death with NGINX PLUS
            if not KCFileUtils.grep(self, '/etc/nginx/fastcgi_params',
                                    'SCRIPT_FILENAME'):
                with open('/etc/nginx/fastcgi_params',
                          encoding='utf-8', mode='a') as kc_nginx:
                    kc_nginx.write('fastcgi_param \tSCRIPT_FILENAME '
                                   '\t$request_filename;\n')
            try:
                data = dict(php="9000", debug="9001",
                            php7="9070", debug7="9170",
                            release=KCVar.kc_version)
                KCTemplate.deploy(
                    self, '{0}/upstream.conf'.format(ngxcnf),
                    'upstream.mustache', data, overwrite=True)

                data = dict(phpconf=(
                    bool(KCAptGet.is_installed(self, 'php7.2-fpm'))),
                    release=KCVar.kc_version)
                KCTemplate.deploy(
                    self, '{0}/stub_status.conf'.format(ngxcnf),
                    'stub_status.mustache', data)
                data = dict(release=KCVar.kc_version)
                KCTemplate.deploy(
                    self, '{0}/webp.conf'.format(ngxcnf),
                    'webp.mustache', data, overwrite=False)
                KCTemplate.deploy(
                    self, '{0}/avif.conf'.format(ngxcnf),
                    'avif.mustache', data, overwrite=False)

                KCTemplate.deploy(
                    self, '{0}/cloudflare.conf'.format(ngxcnf),
                    'cloudflare.mustache', data)

                KCTemplate.deploy(
                    self,
                    '{0}/map-wp-fastcgi-cache.conf'.format(ngxcnf),
                    'map-wp.mustache', data)
            except CommandExecutionError as e:
                Log.debug(self, "{0}".format(e))

            # Setup Nginx common directory
            if not os.path.exists('{0}'.format(ngxcom)):
                Log.debug(self, 'Creating directory'
                          '/etc/nginx/common')
                os.makedirs('/etc/nginx/common')

            try:
                data = dict(release=KCVar.kc_version)

                # Common Configuration
                KCTemplate.deploy(self,
                                  '{0}/locations-kc.conf'
                                  .format(ngxcom),
                                  'locations.mustache', data)

                KCTemplate.deploy(self,
                                  '{0}/wpsubdir.conf'
                                  .format(ngxcom),
                                  'wpsubdir.mustache', data)

                kc_php_version = ["php72", "php73", "php74", "php80" "php81"]
                for kc_php in kc_php_version:
                    data = dict(upstream="{0}".format(kc_php),
                                release=KCVar.kc_version)
                    KCConf.nginxcommon(self)

            except CommandExecutionError as e:
                Log.debug(self, "{0}".format(e))

            with open("/etc/nginx/common/release",
                      "w", encoding='utf-8') as release_file:
                release_file.write("v{0}"
                                   .format(KCVar.kc_version))
            release_file.close()

            # Following files should not be overwrited

            data = dict(webroot=ngxroot, release=KCVar.kc_version)
            KCTemplate.deploy(self,
                              '{0}/acl.conf'
                              .format(ngxcom),
                              'acl.mustache', data, overwrite=False)
            KCTemplate.deploy(self,
                              '{0}/blockips.conf'
                              .format(ngxcnf),
                              'blockips.mustache', data, overwrite=False)
            KCTemplate.deploy(self,
                              '{0}/fastcgi.conf'
                              .format(ngxcnf),
                              'fastcgi.mustache', data, overwrite=True)

            # add redis cache format if not already done
            if (os.path.isfile("/etc/nginx/nginx.conf") and
                not os.path.isfile("/etc/nginx/conf.d"
                                   "/redis.conf")):
                with open("/etc/nginx/conf.d/"
                          "redis.conf", "a") as redis_file:
                    redis_file.write(
                        "# Log format Settings\n"
                        "log_format rt_cache_redis "
                        "'$remote_addr "
                        "$upstream_response_time "
                        "$srcache_fetch_status "
                        "[$time_local] '\n"
                        "'$http_host \"$request\" $status"
                        " $body_bytes_sent '\n"
                        "'\"$http_referer\" "
                        "\"$http_user_agent\"';\n")

            if not os.path.exists('/etc/nginx/bots.d'):
                KCFileUtils.textwrite(
                    self, '/etc/nginx/conf.d/variables-hash.conf',
                    'variables_hash_max_size 4096;\n'
                    'variables_hash_bucket_size 4096;')

                # Nginx-Plus does not have nginx
                # package structure like this
                # So creating directories
            if not os.path.exists('/etc/nginx/sites-available'):
                Log.debug(self, 'Creating directory'
                          '/etc/nginx/sites-available')
                os.makedirs('/etc/nginx/sites-available')

            if not os.path.exists('/etc/nginx/sites-enabled'):
                Log.debug(self, 'Creating directory'
                          '/etc/nginx/sites-available')
                os.makedirs('/etc/nginx/sites-enabled')

            # 22222 port settings
            if os.path.exists('/etc/nginx/sites-available/22222'):
                Log.debug(self, "looking for the current backend port")
                for line in open('/etc/nginx/sites-available/22222',
                                 encoding='utf-8'):
                    if 'listen' in line:
                        listen_line = line.strip()
                        break
                port = (listen_line).split(' ')
                current_backend_port = (port[1]).strip()
            else:
                current_backend_port = '22222'

            if 'current_backend_port' not in locals():
                current_backend_port = '22222'

            data = dict(webroot=ngxroot,
                        release=KCVar.kc_version, port=current_backend_port)
            KCTemplate.deploy(
                self,
                '/etc/nginx/sites-available/22222',
                '22222.mustache', data, overwrite=True)

            passwd = ''.join([random.choice
                              (string.ascii_letters + string.digits)
                              for n in range(24)])
            if not os.path.isfile('/etc/nginx/htpasswd-kc'):
                try:
                    KCShellExec.cmd_exec(
                        self, "printf \"KeepCloud:"
                        "$(openssl passwd -crypt "
                        "{password} 2> /dev/null)\n\""
                        "> /etc/nginx/htpasswd-kc "
                        "2>/dev/null"
                        .format(password=passwd))
                except CommandExecutionError as e:
                    Log.debug(self, "{0}".format(e))
                    Log.error(self, "Failed to save HTTP Auth")
            if not os.path.islink('/etc/nginx/sites-enabled/22222'):
                # Create Symbolic link for 22222
                KCFileUtils.create_symlink(
                    self, ['/etc/nginx/'
                           'sites-available/'
                           '22222',
                           '/etc/nginx/'
                           'sites-enabled/'
                           '22222'])
            # Create log and cert folder and softlinks
            if not os.path.exists('{0}22222/logs'
                                  .format(ngxroot)):
                Log.debug(self, "Creating directory "
                          "{0}22222/logs "
                          .format(ngxroot))
                os.makedirs('{0}22222/logs'
                            .format(ngxroot))

            if not os.path.exists('{0}22222/cert'
                                  .format(ngxroot)):
                Log.debug(self, "Creating directory "
                          "{0}22222/cert"
                          .format(ngxroot))
                os.makedirs('{0}22222/cert'
                            .format(ngxroot))

            if not os.path.isdir('{0}22222/conf/nginx'
                                 .format(ngxroot)):
                Log.debug(self, "Creating directory "
                          "{0}22222/conf/nginx"
                          .format(ngxroot))
                os.makedirs('{0}22222/conf/nginx'
                            .format(ngxroot))

                KCFileUtils.create_symlink(
                    self,
                    ['/var/log/nginx/'
                     '22222.access.log',
                     '{0}22222/'
                     'logs/access.log'
                     .format(ngxroot)]
                )

                KCFileUtils.create_symlink(
                    self,
                    ['/var/log/nginx/'
                     '22222.error.log',
                     '{0}22222/'
                     'logs/error.log'
                     .format(ngxroot)]
                )
            if (not os.path.isfile('{0}22222/cert/22222.key'
                                   .format(ngxroot))):
                SSL.selfsignedcert(self, proftpd=False, backend=True)

            if not os.path.exists('{0}22222/conf/nginx/ssl.conf'
                                  .format(ngxroot)):
                with open("/var/www/22222/conf/nginx/"
                          "ssl.conf", "w") as php_file:
                    php_file.write("ssl_certificate "
                                   "/var/www/22222/cert/22222.crt;\n"
                                   "ssl_certificate_key "
                                   "/var/www/22222/cert/22222.key;\n")

                server_ip = requests.get('http://v4.wordops.eu')

                if set(["nginx"]).issubset(set(apt_packages)):
                    print("Keepcloud backend configuration was successful\n"
                          "You can access it on : https://{0}:22222"
                          .format(server_ip))
                    print("HTTP Auth User Name: KeepCloud" +
                          "\nHTTP Auth Password : {0}".format(passwd))
                    KCService.reload_service(self, 'nginx')
                else:
                    self.msg = (self.msg + ["HTTP Auth User "
                                            "Name: KeepCloud"] +
                                ["HTTP Auth Password : {0}"
                                 .format(passwd)])
                    self.msg = (self.msg + ["KeepCloud backend is available "
                                            "on https://{0}:22222 "
                                            "or https://{1}:22222"
                                            .format(server_ip.text,
                                                    KCVar.kc_fqdn)])

            if not os.path.isfile("/opt/cf-update.sh"):
                data = dict(release=KCVar.kc_version)
                KCTemplate.deploy(self, '/opt/cf-update.sh',
                                  'cf-update.mustache',
                                  data, overwrite=False)
                KCFileUtils.chmod(self, "/opt/cf-update.sh", 0o775)
                KCCron.setcron_weekly(self, '/opt/cf-update.sh '
                                      '> /dev/null 2>&1',
                                      comment='Cloudflare IP refresh cronjob '
                                      'added by KeepCloud')

            # Nginx Configation into GIT
            if not KCService.restart_service(self, 'nginx'):
                try:
                    hashbucket(self)
                    KCService.restart_service(self, 'nginx')
                except Exception:
                    Log.warn(
                        self, "increasing nginx server_names_hash_bucket_size "
                        "do not fix the issue")
                    Log.info(self, "Rolling back to previous configuration")
                    KCGit.rollback(self, ["/etc/nginx"])
                    if not KCService.restart_service(self, 'nginx'):
                        Log.error(
                            self, "There is an error in Nginx configuration.\n"
                            "Use the command nginx -t to identify "
                            "the cause of this issue", False)
            else:
                KCGit.add(self, ["/etc/nginx"], msg="Adding Nginx into Git")
                if not os.path.isdir('/etc/systemd/system/nginx.service.d'):
                    KCFileUtils.mkdir(self,
                                      '/etc/systemd/system/nginx.service.d')
                if not os.path.isdir(
                        '/etc/systemd/system/nginx.service.d/limits.conf'):
                    with open(
                        '/etc/systemd/system/nginx.service.d/limits.conf',
                            encoding='utf-8', mode='w') as ngx_limit:
                        ngx_limit.write('[Service]\nLimitNOFILE=500000')
                    KCShellExec.cmd_exec(self, 'systemctl daemon-reload')
                    KCService.restart_service(self, 'nginx')

        if 'php7.2-fpm' in apt_packages:
            KCGit.add(self, ["/etc/php"], msg="Adding PHP into Git")
            Log.info(self, "Configuring php7.2-fpm")
            ngxroot = '/var/www/'

            # Create log directories
            if not os.path.exists('/var/log/php/7.2/'):
                Log.debug(self, 'Creating directory /var/log/php/7.2/')
                os.makedirs('/var/log/php/7.2/')

            if not os.path.isfile('/etc/php/7.2/fpm/php.ini.orig'):
                KCFileUtils.copyfile(self, '/etc/php/7.2/fpm/php.ini',
                                     '/etc/php/7.2/fpm/php.ini.orig')

            # Parse etc/php/7.2/fpm/php.ini
            config = configparser.ConfigParser()
            Log.debug(self, "configuring php file "
                      "/etc/php/7.2/fpm/php.ini")
            config.read('/etc/php/7.2/fpm/php.ini.orig')
            config['PHP']['expose_php'] = 'Off'
            config['PHP']['post_max_size'] = '100M'
            config['PHP']['upload_max_filesize'] = '100M'
            config['PHP']['max_execution_time'] = '300'
            config['PHP']['max_input_time'] = '300'
            config['PHP']['max_input_vars'] = '20000'
            config['Date']['date.timezone'] = KCVar.kc_timezone
            config['opcache']['opcache.enable'] = '1'
            config['opcache']['opcache.interned_strings_buffer'] = '8'
            config['opcache']['opcache.max_accelerated_files'] = '10000'
            config['opcache']['opcache.memory_consumption'] = '256'
            config['opcache']['opcache.save_comments'] = '1'
            config['opcache']['opcache.revalidate_freq'] = '5'
            config['opcache']['opcache.consistency_checks'] = '0'
            config['opcache']['opcache.validate_timestamps'] = '1'
            with open('/etc/php/7.2/fpm/php.ini',
                      encoding='utf-8', mode='w') as configfile:
                Log.debug(self, "Writting php configuration into "
                          "/etc/php/7.2/fpm/php.ini")
                config.write(configfile)

            # Render php-fpm pool template for php7.3
            data = dict(pid="/run/php/php7.2-fpm.pid",
                        error_log="/var/log/php7.2-fpm.log",
                        include="/etc/php/7.2/fpm/pool.d/*.conf")
            KCTemplate.deploy(
                self, '/etc/php/7.2/fpm/php-fpm.conf',
                'php-fpm.mustache', data)

            data = dict(pool='www-php72', listen='php72-fpm.sock',
                        user='www-data',
                        group='www-data', listenuser='root',
                        listengroup='www-data', openbasedir=True)
            KCTemplate.deploy(self, '/etc/php/7.2/fpm/pool.d/www.conf',
                              'php-pool.mustache', data)
            data = dict(pool='www-two-php72', listen='php72-two-fpm.sock',
                        user='www-data',
                        group='www-data', listenuser='root',
                        listengroup='www-data', openbasedir=True)
            KCTemplate.deploy(self, '/etc/php/7.2/fpm/pool.d/www-two.conf',
                              'php-pool.mustache', data)

            # Generate /etc/php/7.2/fpm/pool.d/debug.conf
            KCFileUtils.copyfile(self, "/etc/php/7.2/fpm/pool.d/www.conf",
                                 "/etc/php/7.2/fpm/pool.d/debug.conf")
            KCFileUtils.searchreplace(self, "/etc/php/7.2/fpm/pool.d/"
                                      "debug.conf", "[www-php72]", "[debug]")
            config = configparser.ConfigParser()
            config.read('/etc/php/7.2/fpm/pool.d/debug.conf')
            config['debug']['listen'] = '127.0.0.1:9172'
            config['debug']['rlimit_core'] = 'unlimited'
            config['debug']['slowlog'] = '/var/log/php/7.2/slow.log'
            config['debug']['request_slowlog_timeout'] = '10s'
            with open('/etc/php/7.2/fpm/pool.d/debug.conf',
                      encoding='utf-8', mode='w') as confifile:
                Log.debug(self, "writting PHP7.2 configuration into "
                          "/etc/php/7.2/fpm/pool.d/debug.conf")
                config.write(confifile)

            with open("/etc/php/7.2/fpm/pool.d/debug.conf",
                      encoding='utf-8', mode='a') as myfile:
                myfile.write("php_admin_value[xdebug.profiler_output_dir] "
                             "= /tmp/ \nphp_admin_value[xdebug.profiler_"
                             "output_name] = cachegrind.out.%p-%H-%R "
                             "\nphp_admin_flag[xdebug.profiler_enable"
                             "_trigger] = on \nphp_admin_flag[xdebug."
                             "profiler_enable] = off\n")

            # Disable xdebug
            if not KCShellExec.cmd_exec(self, "grep -q \';zend_extension\'"
                                        " /etc/php/7.2/mods-available/"
                                        "xdebug.ini"):
                KCFileUtils.searchreplace(self, "/etc/php/7.2/"
                                          "mods-available/"
                                          "xdebug.ini",
                                          "zend_extension",
                                          ";zend_extension")

            # PHP and Debug pull configuration
            if not os.path.exists('{0}22222/htdocs/fpm/status/'
                                  .format(ngxroot)):
                Log.debug(self, 'Creating directory '
                          '{0}22222/htdocs/fpm/status/ '
                          .format(ngxroot))
                os.makedirs('{0}22222/htdocs/fpm/status/'
                            .format(ngxroot))
                open('{0}22222/htdocs/fpm/status/debug72'
                     .format(ngxroot),
                     encoding='utf-8', mode='a').close()
                open('{0}22222/htdocs/fpm/status/php72'
                     .format(ngxroot),
                     encoding='utf-8', mode='a').close()

            # Write info.php
            if not os.path.exists('{0}22222/htdocs/php/'
                                  .format(ngxroot)):
                Log.debug(self, 'Creating directory '
                          '{0}22222/htdocs/php/ '
                          .format(ngxroot))
                os.makedirs('{0}22222/htdocs/php'
                            .format(ngxroot))

                with open("{0}22222/htdocs/php/info.php"
                          .format(ngxroot),
                          encoding='utf-8', mode='w') as myfile:
                    myfile.write("<?php\nphpinfo();\n?>")

            # write opcache clean for php72
            if not os.path.exists('{0}22222/htdocs/cache/opcache'
                                  .format(ngxroot)):
                os.makedirs('{0}22222/htdocs/cache/opcache'
                            .format(ngxroot))
            KCFileUtils.textwrite(
                self, '{0}22222/htdocs/cache/opcache/php72.php'
                .format(ngxroot),
                '<?php opcache_reset(); ?>')

            KCFileUtils.chown(self, "{0}22222/htdocs"
                              .format(ngxroot),
                              'www-data',
                              'www-data', recursive=True)

            # enable imagick php extension
            KCShellExec.cmd_exec(self, 'phpenmod -v ALL imagick')

            # check service restart or rollback configuration
            if not KCService.restart_service(self, 'php7.2-fpm'):
                KCGit.rollback(self, ["/etc/php"], msg="Rollback PHP")
            else:
                KCGit.add(self, ["/etc/php"], msg="Adding PHP into Git")

        # PHP7.3 configuration
        if set(KCVar.kc_php73).issubset(set(apt_packages)):
            KCGit.add(self, ["/etc/php"], msg="Adding PHP into Git")
            Log.info(self, "Configuring php7.3-fpm")
            ngxroot = '/var/www/'
            # Create log directories
            if not os.path.exists('/var/log/php/7.3/'):
                Log.debug(self, 'Creating directory /var/log/php/7.3/')
                os.makedirs('/var/log/php/7.3/')

            if not os.path.isfile('/etc/php/7.3/fpm/php.ini.orig'):
                KCFileUtils.copyfile(self, '/etc/php/7.3/fpm/php.ini',
                                     '/etc/php/7.3/fpm/php.ini.orig')

            # Parse etc/php/7.3/fpm/php.ini
            config = configparser.ConfigParser()
            Log.debug(self, "configuring php file /etc/php/7.3/"
                      "fpm/php.ini")
            config.read('/etc/php/7.3/fpm/php.ini.orig')
            config['PHP']['expose_php'] = 'Off'
            config['PHP']['post_max_size'] = '100M'
            config['PHP']['upload_max_filesize'] = '100M'
            config['PHP']['max_execution_time'] = '300'
            config['PHP']['max_input_time'] = '300'
            config['PHP']['max_input_vars'] = '20000'
            config['Date']['date.timezone'] = KCVar.kc_timezone
            config['opcache']['opcache.enable'] = '1'
            config['opcache']['opcache.interned_strings_buffer'] = '8'
            config['opcache']['opcache.max_accelerated_files'] = '10000'
            config['opcache']['opcache.memory_consumption'] = '256'
            config['opcache']['opcache.save_comments'] = '1'
            config['opcache']['opcache.revalidate_freq'] = '5'
            config['opcache']['opcache.consistency_checks'] = '0'
            config['opcache']['opcache.validate_timestamps'] = '1'
            with open('/etc/php/7.3/fpm/php.ini',
                      encoding='utf-8', mode='w') as configfile:
                Log.debug(self, "Writting php configuration into "
                          "/etc/php/7.3/fpm/php.ini")
                config.write(configfile)

            # Render php-fpm pool template for php7.3
            data = dict(pid="/run/php/php7.3-fpm.pid",
                        error_log="/var/log/php7.3-fpm.log",
                        include="/etc/php/7.3/fpm/pool.d/*.conf")
            KCTemplate.deploy(
                self, '/etc/php/7.3/fpm/php-fpm.conf',
                'php-fpm.mustache', data)

            data = dict(pool='www-php73', listen='php73-fpm.sock',
                        user='www-data',
                        group='www-data', listenuser='root',
                        listengroup='www-data', openbasedir=True)
            KCTemplate.deploy(self, '/etc/php/7.3/fpm/pool.d/www.conf',
                              'php-pool.mustache', data)
            data = dict(pool='www-two-php73', listen='php73-two-fpm.sock',
                        user='www-data',
                        group='www-data', listenuser='root',
                        listengroup='www-data', openbasedir=True)
            KCTemplate.deploy(self, '/etc/php/7.3/fpm/pool.d/www-two.conf',
                              'php-pool.mustache', data)

            # Generate /etc/php/7.3/fpm/pool.d/debug.conf
            KCFileUtils.copyfile(self, "/etc/php/7.3/fpm/pool.d/www.conf",
                                 "/etc/php/7.3/fpm/pool.d/debug.conf")
            KCFileUtils.searchreplace(self, "/etc/php/7.3/fpm/pool.d/"
                                      "debug.conf", "[www-php73]", "[debug]")
            config = configparser.ConfigParser()
            config.read('/etc/php/7.3/fpm/pool.d/debug.conf')
            config['debug']['listen'] = '127.0.0.1:9173'
            config['debug']['rlimit_core'] = 'unlimited'
            config['debug']['slowlog'] = '/var/log/php/7.3/slow.log'
            config['debug']['request_slowlog_timeout'] = '10s'
            with open('/etc/php/7.3/fpm/pool.d/debug.conf',
                      encoding='utf-8', mode='w') as confifile:
                Log.debug(self, "writting PHP 7.3 configuration into "
                          "/etc/php/7.3/fpm/pool.d/debug.conf")
                config.write(confifile)

            with open("/etc/php/7.3/fpm/pool.d/debug.conf",
                      encoding='utf-8', mode='a') as myfile:
                myfile.write(
                    "php_admin_value[xdebug.profiler_output_dir] "
                    "= /tmp/ \nphp_admin_value[xdebug.profiler_"
                    "output_name] = cachegrind.out.%p-%H-%R "
                    "\nphp_admin_flag[xdebug.profiler_enable"
                    "_trigger] = on \nphp_admin_flag[xdebug."
                    "profiler_enable] = off\n")

            # Disable xdebug
            if not KCShellExec.cmd_exec(
                    self, "grep -q \';zend_extension\'"
                    " /etc/php/7.3/mods-available/xdebug.ini"):
                KCFileUtils.searchreplace(
                    self, "/etc/php/7.3/mods-available/"
                    "xdebug.ini",
                    "zend_extension", ";zend_extension")

            # PHP and Debug pull configuration
            if not os.path.exists('{0}22222/htdocs/fpm/status/'
                                  .format(ngxroot)):
                Log.debug(self, 'Creating directory '
                          '{0}22222/htdocs/fpm/status/ '
                          .format(ngxroot))
                os.makedirs('{0}22222/htdocs/fpm/status/'
                            .format(ngxroot))
            open('{0}22222/htdocs/fpm/status/debug73'
                 .format(ngxroot),
                 encoding='utf-8', mode='a').close()
            open('{0}22222/htdocs/fpm/status/php73'
                 .format(ngxroot),
                 encoding='utf-8', mode='a').close()

            # Write info.php
            if not os.path.exists('{0}22222/htdocs/php/'
                                  .format(ngxroot)):
                Log.debug(self, 'Creating directory '
                          '{0}22222/htdocs/php/ '
                          .format(ngxroot))
                os.makedirs('{0}22222/htdocs/php'
                            .format(ngxroot))

            with open("{0}22222/htdocs/php/info.php"
                      .format(ngxroot),
                      encoding='utf-8', mode='w') as myfile:
                myfile.write("<?php\nphpinfo();\n?>")

            # write opcache clean for php73
            if not os.path.exists('{0}22222/htdocs/cache/opcache'
                                  .format(ngxroot)):
                os.makedirs('{0}22222/htdocs/cache/opcache'
                            .format(ngxroot))
            KCFileUtils.textwrite(
                self, '{0}22222/htdocs/cache/opcache/php73.php'
                .format(ngxroot),
                '<?php opcache_reset(); ?>')

            KCFileUtils.chown(self, "{0}22222/htdocs"
                              .format(ngxroot),
                              'www-data',
                              'www-data', recursive=True)

            # enable imagick php extension
            KCShellExec.cmd_exec(self, 'phpenmod -v ALL imagick')

            # check service restart or rollback configuration
            if not KCService.restart_service(self, 'php7.3-fpm'):
                KCGit.rollback(self, ["/etc/php"], msg="Rollback PHP")
            else:
                KCGit.add(self, ["/etc/php"], msg="Adding PHP into Git")

        # PHP7.4 configuration
        # php7.4 configuration
        if set(KCVar.kc_php74).issubset(set(apt_packages)):
            KCGit.add(self, ["/etc/php"], msg="Adding PHP into Git")
            Log.info(self, "Configuring php7.4-fpm")
            ngxroot = '/var/www/'
            # Create log directories
            if not os.path.exists('/var/log/php/7.4/'):
                Log.debug(self, 'Creating directory /var/log/php/7.4/')
                os.makedirs('/var/log/php/7.4/')

            if not os.path.isfile('/etc/php/7.4/fpm/php.ini.orig'):
                KCFileUtils.copyfile(self, '/etc/php/7.4/fpm/php.ini',
                                     '/etc/php/7.4/fpm/php.ini.orig')

            # Parse etc/php/7.4/fpm/php.ini
            config = configparser.ConfigParser()
            Log.debug(self, "configuring php file /etc/php/7.4/"
                      "fpm/php.ini")
            config.read('/etc/php/7.4/fpm/php.ini.orig')
            config['PHP']['expose_php'] = 'Off'
            config['PHP']['post_max_size'] = '100M'
            config['PHP']['upload_max_filesize'] = '100M'
            config['PHP']['max_execution_time'] = '300'
            config['PHP']['max_input_time'] = '300'
            config['PHP']['max_input_vars'] = '20000'
            config['Date']['date.timezone'] = KCVar.kc_timezone
            config['opcache']['opcache.enable'] = '1'
            config['opcache']['opcache.interned_strings_buffer'] = '8'
            config['opcache']['opcache.max_accelerated_files'] = '10000'
            config['opcache']['opcache.memory_consumption'] = '256'
            config['opcache']['opcache.save_comments'] = '1'
            config['opcache']['opcache.revalidate_freq'] = '5'
            config['opcache']['opcache.consistency_checks'] = '0'
            config['opcache']['opcache.validate_timestamps'] = '1'
            config['opcache']['opcache.preload_user'] = 'www-data'
            with open('/etc/php/7.4/fpm/php.ini',
                      encoding='utf-8', mode='w') as configfile:
                Log.debug(self, "Writting php configuration into "
                          "/etc/php/7.4/fpm/php.ini")
                config.write(configfile)

            # Render php-fpm pool template for php7.4
            data = dict(pid="/run/php/php7.4-fpm.pid",
                        error_log="/var/log/php7.4-fpm.log",
                        include="/etc/php/7.4/fpm/pool.d/*.conf")
            KCTemplate.deploy(
                self, '/etc/php/7.4/fpm/php-fpm.conf',
                'php-fpm.mustache', data)

            data = dict(pool='www-php74', listen='php74-fpm.sock',
                        user='www-data',
                        group='www-data', listenuser='root',
                        listengroup='www-data', openbasedir=True)
            KCTemplate.deploy(self, '/etc/php/7.4/fpm/pool.d/www.conf',
                              'php-pool.mustache', data)
            data = dict(pool='www-two-php74', listen='php74-two-fpm.sock',
                        user='www-data',
                        group='www-data', listenuser='root',
                        listengroup='www-data', openbasedir=True)
            KCTemplate.deploy(self, '/etc/php/7.4/fpm/pool.d/www-two.conf',
                              'php-pool.mustache', data)

            # Generate /etc/php/7.4/fpm/pool.d/debug.conf
            KCFileUtils.copyfile(self, "/etc/php/7.4/fpm/pool.d/www.conf",
                                 "/etc/php/7.4/fpm/pool.d/debug.conf")
            KCFileUtils.searchreplace(self, "/etc/php/7.4/fpm/pool.d/"
                                      "debug.conf", "[www-php74]", "[debug]")
            config = configparser.ConfigParser()
            config.read('/etc/php/7.4/fpm/pool.d/debug.conf')
            config['debug']['listen'] = '127.0.0.1:9174'
            config['debug']['rlimit_core'] = 'unlimited'
            config['debug']['slowlog'] = '/var/log/php/7.4/slow.log'
            config['debug']['request_slowlog_timeout'] = '10s'
            with open('/etc/php/7.4/fpm/pool.d/debug.conf',
                      encoding='utf-8', mode='w') as confifile:
                Log.debug(self, "writting PHP 7.4 configuration into "
                          "/etc/php/7.4/fpm/pool.d/debug.conf")
                config.write(confifile)

            with open("/etc/php/7.4/fpm/pool.d/debug.conf",
                      encoding='utf-8', mode='a') as myfile:
                myfile.write(
                    "php_admin_value[xdebug.profiler_output_dir] "
                    "= /tmp/ \nphp_admin_value[xdebug.profiler_"
                    "output_name] = cachegrind.out.%p-%H-%R "
                    "\nphp_admin_flag[xdebug.profiler_enable"
                    "_trigger] = on \nphp_admin_flag[xdebug."
                    "profiler_enable] = off\n")

            # Disable xdebug
            if not KCShellExec.cmd_exec(
                    self, "grep -q \';zend_extension\'"
                    " /etc/php/7.4/mods-available/xdebug.ini"):
                KCFileUtils.searchreplace(
                    self, "/etc/php/7.4/mods-available/"
                    "xdebug.ini",
                    "zend_extension", ";zend_extension")

            # PHP and Debug pull configuration
            if not os.path.exists('{0}22222/htdocs/fpm/status/'
                                  .format(ngxroot)):
                Log.debug(self, 'Creating directory '
                          '{0}22222/htdocs/fpm/status/ '
                          .format(ngxroot))
                os.makedirs('{0}22222/htdocs/fpm/status/'
                            .format(ngxroot))
            open('{0}22222/htdocs/fpm/status/debug74'
                 .format(ngxroot),
                 encoding='utf-8', mode='a').close()
            open('{0}22222/htdocs/fpm/status/php74'
                 .format(ngxroot),
                 encoding='utf-8', mode='a').close()

            # Write info.php
            if not os.path.exists('{0}22222/htdocs/php/'
                                  .format(ngxroot)):
                Log.debug(self, 'Creating directory '
                          '{0}22222/htdocs/php/ '
                          .format(ngxroot))
                os.makedirs('{0}22222/htdocs/php'
                            .format(ngxroot))

            KCFileUtils.textwrite(
                self, "{0}22222/htdocs/php/info.php"
                .format(ngxroot), "<?php\nphpinfo();\n?>")

            # write opcache clean for php74
            if not os.path.exists('{0}22222/htdocs/cache/opcache'
                                  .format(ngxroot)):
                os.makedirs('{0}22222/htdocs/cache/opcache'
                            .format(ngxroot))
            KCFileUtils.textwrite(
                self, '{0}22222/htdocs/cache/opcache/php74.php'
                .format(ngxroot),
                '<?php opcache_reset(); ?>')

            KCFileUtils.chown(self, "{0}22222/htdocs"
                              .format(ngxroot),
                              'www-data',
                              'www-data', recursive=True)

            # enable imagick php extension
            KCShellExec.cmd_exec(self, 'phpenmod -v ALL imagick')

            # check service restart or rollback configuration
            if not KCService.restart_service(self, 'php7.4-fpm'):
                KCGit.rollback(self, ["/etc/php"], msg="Rollback PHP")
            else:
                KCGit.add(self, ["/etc/php"], msg="Adding PHP into Git")

            if os.path.exists('/etc/nginx/conf.d/upstream.conf'):
                if not KCFileUtils.grepcheck(
                        self, '/etc/nginx/conf.d/upstream.conf', 'php74'):
                    data = dict(php="9000", debug="9001",
                                php7="9070", debug7="9170",
                                release=KCVar.kc_version)
                    KCTemplate.deploy(
                        self, '/etc/nginx/conf.d/upstream.conf',
                        'upstream.mustache', data, True)
                    KCConf.nginxcommon(self)

        # php8.0 configuration
        if set(KCVar.kc_php80).issubset(set(apt_packages)):
            KCGit.add(self, ["/etc/php"], msg="Adding PHP into Git")
            Log.info(self, "Configuring php8.0-fpm")
            ngxroot = '/var/www/'
            # Create log directories
            if not os.path.exists('/var/log/php/8.0/'):
                Log.debug(self, 'Creating directory /var/log/php/8.0/')
                os.makedirs('/var/log/php/8.0/')

            if not os.path.isfile('/etc/php/8.0/fpm/php.ini.orig'):
                KCFileUtils.copyfile(self, '/etc/php/8.0/fpm/php.ini',
                                     '/etc/php/8.0/fpm/php.ini.orig')

            # Parse etc/php/8.0/fpm/php.ini
            config = configparser.ConfigParser()
            Log.debug(self, "configuring php file /etc/php/8.0/"
                      "fpm/php.ini")
            config.read('/etc/php/8.0/fpm/php.ini.orig')
            config['PHP']['expose_php'] = 'Off'
            config['PHP']['post_max_size'] = '100M'
            config['PHP']['upload_max_filesize'] = '100M'
            config['PHP']['max_execution_time'] = '300'
            config['PHP']['max_input_time'] = '300'
            config['PHP']['max_input_vars'] = '20000'
            config['Date']['date.timezone'] = KCVar.kc_timezone
            config['opcache']['opcache.enable'] = '1'
            config['opcache']['opcache.interned_strings_buffer'] = '8'
            config['opcache']['opcache.max_accelerated_files'] = '10000'
            config['opcache']['opcache.memory_consumption'] = '256'
            config['opcache']['opcache.save_comments'] = '1'
            config['opcache']['opcache.revalidate_freq'] = '5'
            config['opcache']['opcache.consistency_checks'] = '0'
            config['opcache']['opcache.validate_timestamps'] = '1'
            config['opcache']['opcache.preload_user'] = 'www-data'
            with open('/etc/php/8.0/fpm/php.ini',
                      encoding='utf-8', mode='w') as configfile:
                Log.debug(self, "Writting php configuration into "
                          "/etc/php/8.0/fpm/php.ini")
                config.write(configfile)

            # Render php-fpm pool template for php8.0
            data = dict(pid="/run/php/php8.0-fpm.pid",
                        error_log="/var/log/php8.0-fpm.log",
                        include="/etc/php/8.0/fpm/pool.d/*.conf")
            KCTemplate.deploy(
                self, '/etc/php/8.0/fpm/php-fpm.conf',
                'php-fpm.mustache', data)

            data = dict(pool='www-php80', listen='php80-fpm.sock',
                        user='www-data',
                        group='www-data', listenuser='root',
                        listengroup='www-data', openbasedir=True)
            KCTemplate.deploy(self, '/etc/php/8.0/fpm/pool.d/www.conf',
                              'php-pool.mustache', data)
            data = dict(pool='www-two-php80', listen='php80-two-fpm.sock',
                        user='www-data',
                        group='www-data', listenuser='root',
                        listengroup='www-data', openbasedir=True)
            KCTemplate.deploy(self, '/etc/php/8.0/fpm/pool.d/www-two.conf',
                              'php-pool.mustache', data)

            # Generate /etc/php/8.0/fpm/pool.d/debug.conf
            KCFileUtils.copyfile(self, "/etc/php/8.0/fpm/pool.d/www.conf",
                                 "/etc/php/8.0/fpm/pool.d/debug.conf")
            KCFileUtils.searchreplace(self, "/etc/php/8.0/fpm/pool.d/"
                                      "debug.conf", "[www-php80]", "[debug]")
            config = configparser.ConfigParser()
            config.read('/etc/php/8.0/fpm/pool.d/debug.conf')
            config['debug']['listen'] = '127.0.0.1:9180'
            config['debug']['rlimit_core'] = 'unlimited'
            config['debug']['slowlog'] = '/var/log/php/8.0/slow.log'
            config['debug']['request_slowlog_timeout'] = '10s'
            with open('/etc/php/8.0/fpm/pool.d/debug.conf',
                      encoding='utf-8', mode='w') as confifile:
                Log.debug(self, "writting PHP 8.0 configuration into "
                          "/etc/php/8.0/fpm/pool.d/debug.conf")
                config.write(confifile)

            with open("/etc/php/8.0/fpm/pool.d/debug.conf",
                      encoding='utf-8', mode='a') as myfile:
                myfile.write(
                    "php_admin_value[xdebug.profiler_output_dir] "
                    "= /tmp/ \nphp_admin_value[xdebug.profiler_"
                    "output_name] = cachegrind.out.%p-%H-%R "
                    "\nphp_admin_flag[xdebug.profiler_enable"
                    "_trigger] = on \nphp_admin_flag[xdebug."
                    "profiler_enable] = off\n")

            # Disable xdebug
            if not KCShellExec.cmd_exec(
                    self, "grep -q \';zend_extension\'"
                    " /etc/php/8.0/mods-available/xdebug.ini"):
                KCFileUtils.searchreplace(
                    self, "/etc/php/8.0/mods-available/"
                    "xdebug.ini",
                    "zend_extension", ";zend_extension")

            # PHP and Debug pull configuration
            if not os.path.exists('{0}22222/htdocs/fpm/status/'
                                  .format(ngxroot)):
                Log.debug(self, 'Creating directory '
                          '{0}22222/htdocs/fpm/status/ '
                          .format(ngxroot))
                os.makedirs('{0}22222/htdocs/fpm/status/'
                            .format(ngxroot))
            open('{0}22222/htdocs/fpm/status/debug80'
                 .format(ngxroot),
                 encoding='utf-8', mode='a').close()
            open('{0}22222/htdocs/fpm/status/php80'
                 .format(ngxroot),
                 encoding='utf-8', mode='a').close()

            # Write info.php
            if not os.path.exists('{0}22222/htdocs/php/'
                                  .format(ngxroot)):
                Log.debug(self, 'Creating directory '
                          '{0}22222/htdocs/php/ '
                          .format(ngxroot))
                os.makedirs('{0}22222/htdocs/php'
                            .format(ngxroot))

            KCFileUtils.textwrite(
                self, "{0}22222/htdocs/php/info.php"
                .format(ngxroot), "<?php\nphpinfo();\n?>")

            # write opcache clean for php80
            if not os.path.exists('{0}22222/htdocs/cache/opcache'
                                  .format(ngxroot)):
                os.makedirs('{0}22222/htdocs/cache/opcache'
                            .format(ngxroot))
            KCFileUtils.textwrite(
                self, '{0}22222/htdocs/cache/opcache/php80.php'
                .format(ngxroot),
                '<?php opcache_reset(); ?>')

            KCFileUtils.chown(self, "{0}22222/htdocs"
                              .format(ngxroot),
                              'www-data',
                              'www-data', recursive=True)

            # enable imagick php extension
            KCShellExec.cmd_exec(self, 'phpenmod -v ALL imagick')

            # check service restart or rollback configuration
            if not KCService.restart_service(self, 'php8.0-fpm'):
                KCGit.rollback(self, ["/etc/php"], msg="Rollback PHP")
            else:
                KCGit.add(self, ["/etc/php"], msg="Adding PHP into Git")

            if os.path.exists('/etc/nginx/conf.d/upstream.conf'):
                if not KCFileUtils.grepcheck(
                        self, '/etc/nginx/conf.d/upstream.conf', 'php81'):
                    data = dict(php="9000", debug="9001",
                                php7="9070", debug7="9170",
                                php8="9080", debug8="9180",
                                release=KCVar.kc_version)
                    KCTemplate.deploy(
                        self, '/etc/nginx/conf.d/upstream.conf',
                        'upstream.mustache', data, True)
                    KCConf.nginxcommon(self)

        # php8.1 configuration
        if set(KCVar.kc_php81).issubset(set(apt_packages)):
            KCGit.add(self, ["/etc/php"], msg="Adding PHP into Git")
            Log.info(self, "Configuring php8.1-fpm")
            ngxroot = '/var/www/'
            # Create log directories
            if not os.path.exists('/var/log/php/8.1/'):
                Log.debug(self, 'Creating directory /var/log/php/8.1/')
                os.makedirs('/var/log/php/8.1/')

            if not os.path.isfile('/etc/php/8.1/fpm/php.ini.orig'):
                KCFileUtils.copyfile(self, '/etc/php/8.1/fpm/php.ini',
                                     '/etc/php/8.1/fpm/php.ini.orig')

            # Parse etc/php/8.1/fpm/php.ini
            config = configparser.ConfigParser()
            Log.debug(self, "configuring php file /etc/php/8.1/"
                      "fpm/php.ini")
            config.read('/etc/php/8.1/fpm/php.ini.orig')
            config['PHP']['expose_php'] = 'Off'
            config['PHP']['post_max_size'] = '100M'
            config['PHP']['upload_max_filesize'] = '100M'
            config['PHP']['max_execution_time'] = '300'
            config['PHP']['max_input_time'] = '300'
            config['PHP']['max_input_vars'] = '20000'
            config['Date']['date.timezone'] = KCVar.kc_timezone
            config['opcache']['opcache.enable'] = '1'
            config['opcache']['opcache.interned_strings_buffer'] = '8'
            config['opcache']['opcache.max_accelerated_files'] = '10000'
            config['opcache']['opcache.memory_consumption'] = '256'
            config['opcache']['opcache.save_comments'] = '1'
            config['opcache']['opcache.revalidate_freq'] = '5'
            config['opcache']['opcache.consistency_checks'] = '0'
            config['opcache']['opcache.validate_timestamps'] = '1'
            config['opcache']['opcache.preload_user'] = 'www-data'
            with open('/etc/php/8.1/fpm/php.ini',
                      encoding='utf-8', mode='w') as configfile:
                Log.debug(self, "Writting php configuration into "
                          "/etc/php/8.1/fpm/php.ini")
                config.write(configfile)

            # Render php-fpm pool template for php8.1
            data = dict(pid="/run/php/php8.1-fpm.pid",
                        error_log="/var/log/php8.1-fpm.log",
                        include="/etc/php/8.1/fpm/pool.d/*.conf")
            KCTemplate.deploy(
                self, '/etc/php/8.1/fpm/php-fpm.conf',
                'php-fpm.mustache', data)

            data = dict(pool='www-php81', listen='php81-fpm.sock',
                        user='www-data',
                        group='www-data', listenuser='root',
                        listengroup='www-data', openbasedir=True)
            KCTemplate.deploy(self, '/etc/php/8.1/fpm/pool.d/www.conf',
                              'php-pool.mustache', data)
            data = dict(pool='www-two-php81', listen='php81-two-fpm.sock',
                        user='www-data',
                        group='www-data', listenuser='root',
                        listengroup='www-data', openbasedir=True)
            KCTemplate.deploy(self, '/etc/php/8.1/fpm/pool.d/www-two.conf',
                              'php-pool.mustache', data)

            # Generate /etc/php/8.1/fpm/pool.d/debug.conf
            KCFileUtils.copyfile(self, "/etc/php/8.1/fpm/pool.d/www.conf",
                                 "/etc/php/8.1/fpm/pool.d/debug.conf")
            KCFileUtils.searchreplace(self, "/etc/php/8.1/fpm/pool.d/"
                                      "debug.conf", "[www-php81]", "[debug]")
            config = configparser.ConfigParser()
            config.read('/etc/php/8.1/fpm/pool.d/debug.conf')
            config['debug']['listen'] = '127.0.0.1:9181'
            config['debug']['rlimit_core'] = 'unlimited'
            config['debug']['slowlog'] = '/var/log/php/8.1/slow.log'
            config['debug']['request_slowlog_timeout'] = '10s'
            with open('/etc/php/8.1/fpm/pool.d/debug.conf',
                      encoding='utf-8', mode='w') as confifile:
                Log.debug(self, "writting PHP 8.1 configuration into "
                          "/etc/php/8.1/fpm/pool.d/debug.conf")
                config.write(confifile)

            with open("/etc/php/8.1/fpm/pool.d/debug.conf",
                      encoding='utf-8', mode='a') as myfile:
                myfile.write(
                    "php_admin_value[xdebug.profiler_output_dir] "
                    "= /tmp/ \nphp_admin_value[xdebug.profiler_"
                    "output_name] = cachegrind.out.%p-%H-%R "
                    "\nphp_admin_flag[xdebug.profiler_enable"
                    "_trigger] = on \nphp_admin_flag[xdebug."
                    "profiler_enable] = off\n")

            # Disable xdebug
            if not KCShellExec.cmd_exec(
                    self, "grep -q \';zend_extension\'"
                    " /etc/php/8.1/mods-available/xdebug.ini"):
                KCFileUtils.searchreplace(
                    self, "/etc/php/8.1/mods-available/"
                    "xdebug.ini",
                    "zend_extension", ";zend_extension")

            # PHP and Debug pull configuration
            if not os.path.exists('{0}22222/htdocs/fpm/status/'
                                  .format(ngxroot)):
                Log.debug(self, 'Creating directory '
                          '{0}22222/htdocs/fpm/status/ '
                          .format(ngxroot))
                os.makedirs('{0}22222/htdocs/fpm/status/'
                            .format(ngxroot))
            open('{0}22222/htdocs/fpm/status/debug81'
                 .format(ngxroot),
                 encoding='utf-8', mode='a').close()
            open('{0}22222/htdocs/fpm/status/php81'
                 .format(ngxroot),
                 encoding='utf-8', mode='a').close()

            # Write info.php
            if not os.path.exists('{0}22222/htdocs/php/'
                                  .format(ngxroot)):
                Log.debug(self, 'Creating directory '
                          '{0}22222/htdocs/php/ '
                          .format(ngxroot))
                os.makedirs('{0}22222/htdocs/php'
                            .format(ngxroot))

            KCFileUtils.textwrite(
                self, "{0}22222/htdocs/php/info.php"
                .format(ngxroot), "<?php\nphpinfo();\n?>")

            # write opcache clean for php81
            if not os.path.exists('{0}22222/htdocs/cache/opcache'
                                  .format(ngxroot)):
                os.makedirs('{0}22222/htdocs/cache/opcache'
                            .format(ngxroot))
            KCFileUtils.textwrite(
                self, '{0}22222/htdocs/cache/opcache/php81.php'
                .format(ngxroot),
                '<?php opcache_reset(); ?>')

            KCFileUtils.chown(self, "{0}22222/htdocs"
                              .format(ngxroot),
                              'www-data',
                              'www-data', recursive=True)

            # enable imagick php extension
            KCShellExec.cmd_exec(self, 'phpenmod -v ALL imagick')

            # check service restart or rollback configuration
            if not KCService.restart_service(self, 'php8.1-fpm'):
                KCGit.rollback(self, ["/etc/php"], msg="Rollback PHP")
            else:
                KCGit.add(self, ["/etc/php"], msg="Adding PHP into Git")

            if os.path.exists('/etc/nginx/conf.d/upstream.conf'):
                if not KCFileUtils.grepcheck(
                        self, '/etc/nginx/conf.d/upstream.conf', 'php81'):
                    data = dict(php="9000", debug="9001",
                                php7="9070", debug7="9170",
                                php8="9080", debug8="9180",
                                release=KCVar.kc_version)
                    KCTemplate.deploy(
                        self, '/etc/nginx/conf.d/upstream.conf',
                        'upstream.mustache', data, True)
                    KCConf.nginxcommon(self)

        # create mysql config if it doesn't exist
        if "mariadb-server" in apt_packages:
            KCGit.add(self, ["/etc/mysql"], msg="Adding MySQL into Git")
            if not os.path.exists("/etc/mysql/my.cnf"):
                config = ("[mysqld]\nwait_timeout = 30\n"
                          "interactive_timeout=60\nperformance_schema = 0"
                          "\nquery_cache_type = 1")
                config_file = open("/etc/mysql/my.cnf",
                                   encoding='utf-8', mode='w')
                config_file.write(config)
                config_file.close()
            else:
                # make sure root account have all privileges
                if os.path.exists('/etc/mysql/conf.d/my.cnf.tmp'):
                    try:
                        config = configparser.ConfigParser()
                        config.read('/etc/mysql/conf.d/my.cnf.tmp')
                        chars = config['client']['password']
                        KCShellExec.cmd_exec(
                            self,
                            'mysql -e "SET PASSWORD = '
                            'PASSWORD(\'{0}\'); flush privileges;"'
                            .format(chars))
                        KCFileUtils.mvfile(
                            self, '/etc/mysql/conf.d/my.cnf.tmp',
                            '/etc/mysql/conf.d/my.cnf')
                    except CommandExecutionError:
                        Log.error(self, "Unable to set MySQL password")
                    KCGit.add(self, ["/etc/mysql"],
                              msg="Adding MySQL into Git")
                elif os.path.exists('/etc/mysql/conf.d/my.cnf'):
                    if ((KCAptGet.is_installed(
                        self, 'mariadb-server-10.5')) and
                            not (KCFileUtils.grepcheck(
                                self, '/etc/mysql/conf.d/my.cnf', 'socket'))):
                        try:
                            config = configparser.ConfigParser()
                            config.read('/etc/mysql/conf.d/my.cnf')
                            chars = config['client']['password']
                            KCShellExec.cmd_exec(
                                self,
                                'mysql -e "ALTER USER root@localhost '
                                'IDENTIFIED VIA unix_socket OR '
                                'mysql_native_password; '
                                'SET PASSWORD = PASSWORD(\'{0}\'); '
                                'flush privileges;"'.format(chars))
                            KCFileUtils.textappend(
                                self, '/etc/mysql/conf.d/my.cnf',
                                'socket = /run/mysqld/mysqld.sock')
                        except CommandExecutionError:
                            Log.error(self, "Unable to set MySQL password")
                        KCGit.add(self, ["/etc/mysql"],
                                  msg="Adding MySQL into Git")

                Log.wait(self, "Tuning MariaDB configuration")
                if not os.path.isfile("/etc/mysql/my.cnf.default-pkg"):
                    KCFileUtils.copyfile(self, "/etc/mysql/my.cnf",
                                         "/etc/mysql/my.cnf.default-pkg")
                kc_ram = psutil.virtual_memory().total / (1024 * 1024)
                # set InnoDB variable depending on the RAM available
                kc_ram_innodb = int(kc_ram * 0.3)
                kc_ram_log_buffer = int(kc_ram_innodb * 0.25)
                kc_ram_log_size = int(kc_ram_log_buffer * 0.5)
                if (kc_ram < 2000):
                    kc_innodb_instance = int(1)
                    tmp_table_size = int(32)
                elif (kc_ram > 2000) and (kc_ram < 64000):
                    kc_innodb_instance = int(kc_ram / 1000)
                    tmp_table_size = int(128)
                elif (kc_ram > 64000):
                    kc_innodb_instance = int(64)
                    tmp_table_size = int(256)
                mariadbconf = bool(not os.path.exists(
                    '/etc/mysql/mariadb.conf.d/50-server.cnf'))
                data = dict(
                    tmp_table_size=tmp_table_size, inno_log=kc_ram_log_size,
                    inno_buffer=kc_ram_innodb,
                    inno_log_buffer=kc_ram_log_buffer,
                    innodb_instances=kc_innodb_instance,
                    newmariadb=mariadbconf, release=KCVar.kc_version)
                if os.path.exists('/etc/mysql/mariadb.conf.d/50-server.cnf'):
                    KCTemplate.deploy(
                        self, '/etc/mysql/mariadb.conf.d/50-server.cnf',
                        'my.mustache', data)
                else:
                    KCTemplate.deploy(
                        self, '/etc/mysql/my.cnf', 'my.mustache', data)
                # replacing default values
                Log.debug(self, "Tuning MySQL configuration")
                if os.path.isdir('/etc/systemd/system/mariadb.service.d'):
                    if not os.path.isfile(
                            '/etc/systemd/system/'
                            'mariadb.service.d/limits.conf'):
                        KCFileUtils.textwrite(
                            self,
                            '/etc/systemd/system/'
                            'mariadb.service.d/limits.conf',
                            '[Service]\nLimitNOFILE=500000')
                        KCShellExec.cmd_exec(self, 'systemctl daemon-reload')
                Log.valide(self, "Tuning MySQL configuration")
                # set innodb_buffer_pool_instances depending
                # on the amount of RAM

                KCService.restart_service(self, 'mysql')

                # KCFileUtils.mvfile(self, '/var/lib/mysql/ib_logfile0',
                #                    '/var/lib/mysql/ib_logfile0.bak')
                # KCFileUtils.mvfile(self, '/var/lib/mysql/ib_logfile1',
                #                    '/var/lib/mysql/ib_logfile1.bak')

            KCCron.setcron_weekly(self, 'mysqlcheck -Aos --auto-repair '
                                  '> /dev/null 2>&1',
                                  comment='MySQL optimization cronjob '
                                  'added by KeepCloud')
            KCGit.add(self, ["/etc/mysql"], msg="Adding MySQL into Git")

        # create fail2ban configuration files
        if "fail2ban" in apt_packages:
            KCService.restart_service(self, 'fail2ban')
            if os.path.exists('/etc/fail2ban'):
                KCGit.add(self, ["/etc/fail2ban"],
                          msg="Adding Fail2ban into Git")
                Log.info(self, "Configuring Fail2Ban")
                nginxf2b = bool(os.path.exists('/var/log/nginx'))
                data = dict(release=KCVar.kc_version, nginx=nginxf2b)
                KCTemplate.deploy(
                    self,
                    '/etc/fail2ban/jail.d/custom.conf',
                    'fail2ban.mustache',
                    data, overwrite=True)
                KCTemplate.deploy(
                    self,
                    '/etc/fail2ban/filter.d/kc-keepcloud.conf',
                    'fail2ban-wp.mustache',
                    data, overwrite=False)
                KCTemplate.deploy(
                    self,
                    '/etc/fail2ban/filter.d/nginx-forbidden.conf',
                    'fail2ban-forbidden.mustache',
                    data, overwrite=False)

                if not KCShellExec.cmd_exec(self, 'fail2ban-client reload'):
                    KCGit.rollback(
                        self, ['/etc/fail2ban'], msg="Rollback f2b config")
                    KCService.restart_service(self, 'fail2ban')
                else:
                    KCGit.add(self, ["/etc/fail2ban"],
                              msg="Adding Fail2ban into Git")

        # Proftpd configuration
        if "proftpd-basic" in apt_packages:
            KCGit.add(self, ["/etc/proftpd"],
                      msg="Adding ProFTPd into Git")
            if os.path.isfile("/etc/proftpd/proftpd.conf"):
                Log.debug(self, "Setting up Proftpd configuration")
                KCFileUtils.searchreplace(
                    self, "/etc/proftpd/proftpd.conf",
                    "# DefaultRoot", "DefaultRoot")
                KCFileUtils.searchreplace(
                    self, "/etc/proftpd/proftpd.conf",
                    "# RequireValidShell", "RequireValidShell")
                KCFileUtils.searchreplace(
                    self, "/etc/proftpd/proftpd.conf",
                    "# PassivePorts                  "
                    "49152 65534",
                    "PassivePorts              "
                    "    49000 50000")
            # proftpd TLS configuration
            if not os.path.isdir("/etc/proftpd/ssl"):
                KCFileUtils.mkdir(self, "/etc/proftpd/ssl")
                SSL.selfsignedcert(self, proftpd=True, backend=False)
            KCFileUtils.chmod(self, "/etc/proftpd/ssl/proftpd.key", 0o700)
            KCFileUtils.chmod(self, "/etc/proftpd/ssl/proftpd.crt", 0o700)
            data = dict()
            KCTemplate.deploy(self, '/etc/proftpd/tls.conf',
                              'proftpd-tls.mustache', data)
            KCFileUtils.searchreplace(self, "/etc/proftpd/"
                                      "proftpd.conf",
                                      "#Include /etc/proftpd/tls.conf",
                                      "Include /etc/proftpd/tls.conf")
            KCService.restart_service(self, 'proftpd')

            if os.path.isfile('/etc/ufw/ufw.conf'):
                # add rule for proftpd with UFW
                if KCFileUtils.grepcheck(
                        self, '/etc/ufw/ufw.conf', 'ENABLED=yes'):
                    try:
                        KCShellExec.cmd_exec(
                            self, "ufw limit 21")
                        KCShellExec.cmd_exec(
                            self, "ufw allow 49000:50000/tcp")
                        KCShellExec.cmd_exec(
                            self, "ufw reload")
                    except Exception as e:
                        Log.debug(self, "{0}".format(e))
                        Log.error(self, "Unable to add UFW rules")

            if ((os.path.exists("/etc/fail2ban/jail.d/custom.conf")) and
                (not KCFileUtils.grepcheck(
                    self, "/etc/fail2ban/jail.d/custom.conf",
                    "proftpd"))):
                with open("/etc/fail2ban/jail.d/custom.conf",
                          encoding='utf-8', mode='a') as f2bproftpd:
                    f2bproftpd.write("\n\n[proftpd]\nenabled = true\n")
                KCService.reload_service(self, 'fail2ban')

            if not KCService.reload_service(self, 'proftpd'):
                KCGit.rollback(self, ["/etc/proftpd"],
                               msg="Rollback ProFTPd")
            else:
                KCGit.add(self, ["/etc/proftpd"],
                          msg="Adding ProFTPd into Git")

        # Sendmail configuration
        if "sendmail" in apt_packages:
            if (os.path.exists("/usr/bin/yes") and
                    os.path.exists("/usr/sbin/sendmailconfig")):
                Log.wait(self, "Configuring Sendmail")
                if KCShellExec.cmd_exec(self, "yes 'y' | sendmailconfig"):
                    Log.valide(self, "Configuring Sendmail")
                else:
                    Log.failed(self, "Configuring Sendmail")

        if "ufw" in apt_packages:
            # check if ufw is already enabled
            if not KCFileUtils.grep(self,
                                    '/etc/ufw/ufw.conf', 'ENABLED=yes'):
                Log.wait(self, "Configuring UFW")
                # check if ufw script is already created
                if not os.path.isfile("/opt/ufw.sh"):
                    data = dict()
                    KCTemplate.deploy(self, '/opt/ufw.sh',
                                      'ufw.mustache',
                                      data, overwrite=False)
                    KCFileUtils.chmod(self, "/opt/ufw.sh", 0o700)
                # setup ufw rules
                KCShellExec.cmd_exec(self, "bash /opt/ufw.sh")
                Log.valide(self, "Configuring UFW")
            else:
                Log.info(self, "UFW is already installed and enabled")

        # Redis configuration
        if "redis-server" in apt_packages:
            if os.path.isfile("/etc/nginx/conf.d/upstream.conf"):
                if not KCFileUtils.grep(self, "/etc/nginx/conf.d/"
                                        "upstream.conf",
                                        "redis"):
                    with open("/etc/nginx/conf.d/upstream.conf",
                              "a") as redis_file:
                        redis_file.write("upstream redis {\n"
                                         "    server 127.0.0.1:6379;\n"
                                         "    keepalive 10;\n}\n")

            if os.path.isfile("/etc/nginx/nginx.conf"):
                if not os.path.isfile("/etc/nginx/conf.d/redis.conf"):
                    with open("/etc/nginx/conf.d/redis.conf",
                              "a") as redis_file:
                        redis_file.write(
                            "# Log format Settings\n"
                            "log_format rt_cache_redis '$remote_addr "
                            "$upstream_response_time $srcache_fetch_status "
                            "[$time_local] '\n '$http_host \"$request\" "
                            "$status $body_bytes_sent '\n'\"$http_referer\" "
                            "\"$http_user_agent\"';\n")
            # set redis.conf parameter
            # set maxmemory 10% for ram below 512MB and 20% for others
            # set maxmemory-policy allkeys-lru
            # enable systemd service
            KCGit.add(self, ["/etc/redis"],
                      msg="Adding Redis into Git")
            Log.debug(self, "Enabling redis systemd service")
            KCShellExec.cmd_exec(self, "systemctl enable redis-server")
            if (os.path.isfile("/etc/redis/redis.conf") and
                    (not KCFileUtils.grep(self, "/etc/redis/redis.conf",
                                          "KeepCloud"))):
                Log.wait(self, "Tuning Redis configuration")
                with open("/etc/redis/redis.conf",
                          "a") as redis_file:
                    redis_file.write("\n# KeepCloud v1.0\n")
                kc_ram = psutil.virtual_memory().total / (1024 * 1024)
                if kc_ram < 1024:
                    Log.debug(self, "Setting maxmemory variable to "
                              "{0} in redis.conf"
                              .format(int(kc_ram * 1024 * 1024 * 0.1)))
                    KCFileUtils.searchreplace(
                        self,
                        "/etc/redis/redis.conf",
                        "# maxmemory <bytes>",
                        "maxmemory {0}"
                        .format
                        (int(kc_ram * 1024 * 1024 * 0.1)))

                else:
                    Log.debug(self, "Setting maxmemory variable to {0} "
                              "in redis.conf"
                              .format(int(kc_ram * 1024 * 1024 * 0.2)))
                    KCFileUtils.searchreplace(
                        self,
                        "/etc/redis/redis.conf",
                        "# maxmemory <bytes>",
                        "maxmemory {0}"
                        .format
                        (int(kc_ram * 1024 * 1024 * 0.2)))

                Log.debug(
                    self, "Setting maxmemory-policy variable to "
                    "allkeys-lru in redis.conf")
                KCFileUtils.searchreplace(
                    self, "/etc/redis/redis.conf",
                    "# maxmemory-policy noeviction",
                    "maxmemory-policy allkeys-lru")
                Log.debug(
                    self, "Setting tcp-backlog variable to "
                    "in redis.conf")
                KCFileUtils.searchreplace(self,
                                          "/etc/redis/redis.conf",
                                          "tcp-backlog 511",
                                          "tcp-backlog 32768")
                KCFileUtils.chown(self, '/etc/redis/redis.conf',
                                  'redis', 'redis', recursive=False)
                Log.valide(self, "Tuning Redis configuration")
            if not KCService.restart_service(self, 'redis-server'):
                KCGit.rollback(self, ["/etc/redis"], msg="Rollback Redis")
            else:
                KCGit.add(self, ["/etc/redis"], msg="Adding Redis into Git")

        # ClamAV configuration
        if set(KCVar.kc_clamav).issubset(set(apt_packages)):
            Log.debug(self, "Setting up freshclam cronjob")
            if not os.path.isfile("/opt/freshclam.sh"):
                data = dict()
                KCTemplate.deploy(self, '/opt/freshclam.sh',
                                  'freshclam.mustache',
                                  data, overwrite=False)
                KCFileUtils.chmod(self, "/opt/freshclam.sh", 0o775)
                KCCron.setcron_weekly(self, '/opt/freshclam.sh '
                                      '> /dev/null 2>&1',
                                      comment='ClamAV freshclam cronjob '
                                      'added by KeepCloud')

        # nanorc
        if 'nano' in apt_packages:
            Log.debug(self, 'Setting up nanorc')
            KCGit.clone(self, 'https://github.com/scopatz/nanorc.git',
                        '/usr/share/nano-syntax-highlighting')
            if os.path.exists('/etc/nanorc'):
                Log.debug(
                    self, 'including nano syntax highlighting to /etc/nanorc')
                if not KCFileUtils.grepcheck(self, '/etc/nanorc',
                                             'nano-syntax-highlighting'):
                    KCFileUtils.textappend(
                        self, '/etc/nanorc', 'include /usr/share/'
                        'nano-syntax-highlighting/*.nanorc')

    if (packages):
        # WP-CLI
        if any('/usr/local/bin/wp' == x[1] for x in packages):
            Log.debug(self, "Setting Privileges"
                      " to /usr/local/bin/wp file ")
            KCFileUtils.chmod(self, "/usr/local/bin/wp", 0o775)

        # PHPMyAdmin
        if any('/var/lib/kc/tmp/pma.tar.gz' == x[1]
               for x in packages):
            kc_phpmyadmin = KCDownload.pma_release(self)
            KCExtract.extract(
                self, '/var/lib/kc/tmp/pma.tar.gz', '/var/lib/kc/tmp/')
            Log.debug(self, 'Extracting file /var/lib/kc/tmp/pma.tar.gz to '
                      'location /var/lib/kc/tmp/')
            if not os.path.exists('{0}22222/htdocs/db'
                                  .format(KCVar.kc_webroot)):
                Log.debug(self, "Creating new  directory "
                          "{0}22222/htdocs/db"
                          .format(KCVar.kc_webroot))
                os.makedirs('{0}22222/htdocs/db'
                            .format(KCVar.kc_webroot))
            if not os.path.exists('{0}22222/htdocs/db/pma/'
                                  .format(KCVar.kc_webroot)):
                shutil.move('/var/lib/kc/tmp/phpMyAdmin-{0}'
                            '-all-languages/'
                            .format(kc_phpmyadmin),
                            '{0}22222/htdocs/db/pma/'
                            .format(KCVar.kc_webroot))
                shutil.copyfile('{0}22222/htdocs/db/pma'
                                '/config.sample.inc.php'
                                .format(KCVar.kc_webroot),
                                '{0}22222/htdocs/db/pma/config.inc.php'
                                .format(KCVar.kc_webroot))
                Log.debug(self, 'Setting Blowfish Secret Key '
                          'FOR COOKIE AUTH to  '
                          '{0}22222/htdocs/db/pma/config.inc.php file '
                          .format(KCVar.kc_webroot))
                blowfish_key = ''.join([random.choice
                                        (string.ascii_letters +
                                         string.digits)
                                        for n in range(32)])
                KCFileUtils.searchreplace(self,
                                          '{0}22222/htdocs/db/pma'
                                          '/config.inc.php'
                                          .format(KCVar.kc_webroot),
                                          "$cfg[\'blowfish_secret\']"
                                          " = \'\';",
                                          "$cfg[\'blowfish_secret\']"
                                          " = \'{0}\';"
                                          .format(blowfish_key))
                Log.debug(self, 'Setting HOST Server For Mysql to  '
                          '{0}22222/htdocs/db/pma/config.inc.php file '
                          .format(KCVar.kc_webroot))
                KCFileUtils.searchreplace(self,
                                          '{0}22222/htdocs/db/pma'
                                          '/config.inc.php'
                                          .format(KCVar.kc_webroot),
                                          "$cfg[\'Servers\'][$i][\'host\']"
                                          " = \'localhost\';", "$cfg"
                                          "[\'Servers\'][$i][\'host\'] "
                                          "= \'{0}\';"
                                          .format(KCVar.kc_mysql_host))
                Log.debug(self, 'Setting Privileges of webroot permission to  '
                          '{0}22222/htdocs/db/pma file '
                          .format(KCVar.kc_webroot))
                KCFileUtils.chown(self, '{0}22222/htdocs'
                                  .format(KCVar.kc_webroot),
                                  'www-data',
                                  'www-data',
                                  recursive=True)

        # composer install and phpmyadmin update
        if any('/var/lib/kc/tmp/composer-install' == x[1]
               for x in packages):
            Log.wait(self, "Installing composer")
            KCShellExec.cmd_exec(self, "php -q /var/lib/kc"
                                 "/tmp/composer-install "
                                 "--install-dir=/var/lib/kc/tmp/")
            shutil.copyfile('/var/lib/kc/tmp/composer.phar',
                            '/usr/local/bin/composer')
            KCFileUtils.chmod(self, "/usr/local/bin/composer", 0o775)
            Log.valide(self, "Installing composer")
            if ((os.path.isdir("/var/www/22222/htdocs/db/pma")) and
                    (not os.path.isfile('/var/www/22222/htdocs/db/'
                                        'pma/composer.lock'))):
                Log.wait(self, "Updating phpMyAdmin")
                KCShellExec.cmd_exec(
                    self, "/usr/local/bin/composer update "
                    "--no-plugins --no-scripts -n --no-dev -d "
                    "/var/www/22222/htdocs/db/pma/")
                KCFileUtils.chown(
                    self, '{0}22222/htdocs/db/pma'
                    .format(KCVar.kc_webroot),
                    'www-data',
                    'www-data',
                    recursive=True)
                Log.valide(self, "Updating phpMyAdmin")
            if not os.path.exists('{0}22222/htdocs/cache/'
                                  'redis/phpRedisAdmin'
                                  .format(KCVar.kc_webroot)):
                Log.debug(self, "Creating new directory "
                          "{0}22222/htdocs/cache/redis"
                          .format(KCVar.kc_webroot))
                os.makedirs('{0}22222/htdocs/cache/redis/phpRedisAdmin'
                            .format(KCVar.kc_webroot))
            if not os.path.isfile('/var/www/22222/htdocs/cache/redis/'
                                  'phpRedisAdmin/composer.lock'):
                KCShellExec.cmd_exec(
                    self, "/usr/local/bin/composer "
                    "create-project --no-plugins --no-scripts -n -s dev "
                    "erik-dubbelboer/php-redis-admin "
                    "/var/www/22222/htdocs/cache/redis/phpRedisAdmin")
            KCFileUtils.chown(self, '{0}22222/htdocs'
                              .format(KCVar.kc_webroot),
                              'www-data',
                              'www-data',
                              recursive=True)

        # MySQLtuner
        if any('/usr/bin/mysqltuner' == x[1]
               for x in packages):
            Log.debug(self, "CHMOD MySQLTuner in /usr/bin/mysqltuner")
            KCFileUtils.chmod(self, "/usr/bin/mysqltuner", 0o775)

        # cheat.sh
        if any('/usr/local/bin/cht.sh' == x[1]
               for x in packages):
            Log.debug(self, "CHMOD cht.sh in /usr/local/bin/cht.sh")
            KCFileUtils.chmod(self, "/usr/local/bin/cht.sh", 0o775)
            if KCFileUtils.grepcheck(self, '/etc/bash_completion.d/cht.sh',
                                     'cht_complete cht.sh'):
                KCFileUtils.searchreplace(
                    self, '/etc/bash_completion.d/cht.sh',
                    '_cht_complete cht.sh',
                    '_cht_complete cheat')
            if not os.path.islink('/usr/local/bin/cheat'):
                KCFileUtils.create_symlink(
                    self, ['/usr/local/bin/cht.sh', '/usr/local/bin/cheat'])

        # netdata install
        if any('/var/lib/kc/tmp/kickstart.sh' == x[1]
               for x in packages):
            Log.wait(self, "Installing Netdata")
            KCShellExec.cmd_exec(
                self, "bash /var/lib/kc/tmp/kickstart.sh "
                "--dont-wait --no-updates --static-only",
                errormsg='', log=False)
            Log.valide(self, "Installing Netdata")
            if os.path.isdir('/etc/netdata'):
                kc_netdata = "/"
            elif os.path.isdir('/opt/netdata'):
                kc_netdata = "/opt/netdata/"
            # disable mail notifications
            KCFileUtils.searchreplace(
                self, "{0}etc/netdata/orig/health_alarm_notify.conf"
                .format(kc_netdata),
                'SEND_EMAIL="YES"',
                'SEND_EMAIL="NO"')
            # make changes persistant
            KCFileUtils.copyfile(
                self, "{0}etc/netdata/orig/"
                "health_alarm_notify.conf"
                .format(kc_netdata),
                "{0}etc/netdata/health_alarm_notify.conf"
                .format(kc_netdata))
            # check if mysql credentials are available
            if KCShellExec.cmd_exec(self, "mysqladmin ping"):
                try:
                    KCMysql.execute(
                        self,
                        "DELETE FROM mysql.user WHERE User = 'netdata';",
                        log=False)
                    KCMysql.execute(
                        self,
                        "create user 'netdata'@'127.0.0.1';",
                        log=False)
                    KCMysql.execute(
                        self,
                        "grant usage on *.* to 'netdata'@'127.0.0.1';",
                        log=False)
                    KCMysql.execute(
                        self, "flush privileges;",
                        log=False)
                except Exception as e:
                    Log.debug(self, "{0}".format(e))
                    Log.info(
                        self, "fail to setup mysql user for netdata")
            KCFileUtils.chown(self, '{0}etc/netdata'
                              .format(kc_netdata),
                              'netdata',
                              'netdata',
                              recursive=True)
            KCService.restart_service(self, 'netdata')

        # KeepCloud Dashboard
        if any('/var/lib/kc/tmp/kc-dashboard.tar.gz' == x[1]
               for x in packages):
            Log.debug(self, "Extracting kc-dashboard.tar.gz "
                      "to location {0}22222/htdocs/"
                      .format(KCVar.kc_webroot))
            KCExtract.extract(self, '/var/lib/kc/tmp/'
                              'kc-dashboard.tar.gz',
                              '{0}22222/htdocs'
                              .format(KCVar.kc_webroot))
            kc_wan = os.popen("/sbin/ip -4 route get 8.8.8.8 | "
                              "grep -oP \"dev [^[:space:]]+ \" "
                              "| cut -d ' ' -f 2").read()
            if (kc_wan != 'eth0' and kc_wan != ''):
                KCFileUtils.searchreplace(self,
                                          "{0}22222/htdocs/index.html"
                                          .format(KCVar.kc_webroot),
                                          "eth0",
                                          "{0}".format(kc_wan))
                Log.debug(self, "Setting Privileges to "
                          "{0}22222/htdocs"
                          .format(KCVar.kc_webroot))
                KCFileUtils.chown(self, '{0}22222/htdocs'
                                  .format(KCVar.kc_webroot),
                                  'www-data',
                                  'www-data',
                                  recursive=True)

        # Extplorer FileManager
        if any('/var/lib/kc/tmp/extplorer.tar.gz' == x[1]
               for x in packages):
            Log.debug(self, "Extracting extplorer.tar.gz "
                      "to location {0}22222/htdocs/files"
                      .format(KCVar.kc_webroot))
            KCExtract.extract(self, '/var/lib/kc/tmp/extplorer.tar.gz',
                              '/var/libkc/tmp/')
            shutil.move('/var/lib/kc/tmp/extplorer-{0}'
                        .format(KCVar.kc_extplorer),
                        '{0}22222/htdocs/files'
                        .format(KCVar.kc_webroot))
            Log.debug(self, "Setting Privileges to "
                      "{0}22222/htdocs/files"
                      .format(KCVar.kc_webroot))
            KCFileUtils.chown(self, '{0}22222/htdocs'
                              .format(KCVar.kc_webroot),
                              'www-data',
                              'www-data',
                              recursive=True)

        # webgrind
        if any('/var/lib/kc/tmp/webgrind.tar.gz' == x[1]
               for x in packages):
            Log.debug(self, "Extracting file webgrind.tar.gz to "
                      "location /var/lib/kc/tmp/ ")
            KCExtract.extract(
                self, '/var/lib/kc/tmp/webgrind.tar.gz',
                '/var/lib/kc/tmp/')
            if not os.path.exists('{0}22222/htdocs/php'
                                  .format(KCVar.kc_webroot)):
                Log.debug(self, "Creating directroy "
                          "{0}22222/htdocs/php"
                          .format(KCVar.kc_webroot))
                os.makedirs('{0}22222/htdocs/php'
                            .format(KCVar.kc_webroot))
            if not os.path.exists('{0}22222/htdocs/php/webgrind'
                                  .format(KCVar.kc_webroot)):
                shutil.move('/var/lib/kc/tmp/webgrind-master/',
                            '{0}22222/htdocs/php/webgrind'
                            .format(KCVar.kc_webroot))

            KCFileUtils.searchreplace(
                self, "{0}22222/htdocs/php/webgrind/"
                "config.php"
                .format(KCVar.kc_webroot),
                "/usr/local/bin/dot", "/usr/bin/dot")
            KCFileUtils.searchreplace(
                self, "{0}22222/htdocs/php/webgrind/"
                "config.php"
                .format(KCVar.kc_webroot),
                "Europe/Copenhagen",
                KCVar.kc_timezone)

            KCFileUtils.searchreplace(
                self, "{0}22222/htdocs/php/webgrind/"
                "config.php"
                .format(KCVar.kc_webroot),
                "90", "100")

            Log.debug(self, "Setting Privileges of webroot permission to "
                      "{0}22222/htdocs/php/webgrind/ file "
                      .format(KCVar.kc_webroot))
            KCFileUtils.chown(self, '{0}22222/htdocs'
                              .format(KCVar.kc_webroot),
                              'www-data',
                              'www-data',
                              recursive=True)
        # anemometer
        if any('/var/lib/kc/tmp/anemometer.tar.gz' == x[1]
               for x in packages):
            Log.debug(self, "Extracting file anemometer.tar.gz to "
                      "location /var/lib/kc/tmp/ ")
            KCExtract.extract(
                self, '/var/lib/kc/tmp/anemometer.tar.gz',
                '/var/lib/kc/tmp/')
            if not os.path.exists('{0}22222/htdocs/db/'
                                  .format(KCVar.kc_webroot)):
                Log.debug(self, "Creating directory")
                os.makedirs('{0}22222/htdocs/db/'
                            .format(KCVar.kc_webroot))
            if not os.path.exists('{0}22222/htdocs/db/anemometer'
                                  .format(KCVar.kc_webroot)):
                shutil.move('/var/lib/kc/tmp/Anemometer-master',
                            '{0}22222/htdocs/db/anemometer'
                            .format(KCVar.kc_webroot))
                chars = ''.join(random.sample(string.ascii_letters, 8))
                try:
                    KCShellExec.cmd_exec(self, 'mysql < {0}22222/htdocs/db'
                                         '/anemometer/install.sql'
                                         .format(KCVar.kc_webroot))
                except Exception as e:
                    Log.debug(self, "{0}".format(e))
                    Log.error(self, "failed to configure Anemometer",
                              exit=False)
                if self.app.config.has_section('mysql'):
                    kc_grant_host = self.app.config.get('mysql', 'grant-host')
                else:
                    kc_grant_host = 'localhost'
                KCMysql.execute(self, 'grant select on'
                                ' *.* to \'anemometer\''
                                '@\'{0}\' IDENTIFIED'
                                ' BY \'{1}\''.format(kc_grant_host,
                                                     chars))
                Log.debug(self, "grant all on slow-query-log.*"
                          " to anemometer@root_user"
                          " IDENTIFIED BY password ")
                KCMysql.execute(
                    self, 'grant all on slow_query_log.* to'
                    '\'anemometer\'@\'{0}\' IDENTIFIED'
                    ' BY \'{1}\''.format(self.app.config.get(
                        'mysql', 'grant-host'),
                        chars),
                    errormsg="cannot grant priviledges",
                    log=False)

                # Custom Anemometer configuration
                Log.debug(self, "configration Anemometer")
                data = dict(host=KCVar.kc_mysql_host, port='3306',
                            user='anemometer', password=chars)
                KCTemplate.deploy(self, '{0}22222/htdocs/db/anemometer'
                                  '/conf/config.inc.php'
                                  .format(KCVar.kc_webroot),
                                  'anemometer.mustache', data)

        # pt-query-advisor
        if any('/usr/bin/pt-query-advisor' == x[1]
               for x in packages):
            KCFileUtils.chmod(self, "/usr/bin/pt-query-advisor", 0o775)

        # ngxblocker
        if any('/usr/local/sbin/install-ngxblocker' == x[1]
               for x in packages):
            # remove duplicate directives
            if os.path.exists('/etc/nginx/conf.d/variables-hash.conf'):
                KCFileUtils.rm(self, '/etc/nginx/conf.d/variables-hash.conf')
            KCFileUtils.chmod(
                self, "/usr/local/sbin/install-ngxblocker", 0o700)
            KCShellExec.cmd_exec(self, '/usr/local/sbin/install-ngxblocker -x')
            KCFileUtils.chmod(
                self, "/usr/local/sbin/update-ngxblocker", 0o700)
            if not KCService.restart_service(self, 'nginx'):
                Log.error(self, 'ngxblocker install failed')


def pre_stack(self):
    """Inital server configuration and tweak"""
    # remove old sysctl tweak
    if os.path.isfile('/etc/sysctl.d/60-ubuntu-nginx-web-server.conf'):
        KCFileUtils.rm(
            self, '/etc/sysctl.d/60-ubuntu-nginx-web-server.conf')
    # check if version.txt exist
    if os.path.exists('/var/lib/kc/version.txt'):
        with open('/var/lib/kc/version.txt',
                  mode='r', encoding='utf-8') as kc_ver:
            # check version written in version.txt
            kc_check = bool(kc_ver.read().strip() ==
                            '{0}'.format(KCVar.kc_version))
    else:
        kc_check = False
    if kc_check is False:
        # kc sysctl tweaks
        # check system type
        kc_arch = bool((os.uname()[4]) == 'x86_64')
        if os.path.isfile('/proc/1/environ'):
            # detect lxc containers
            kc_lxc = KCFileUtils.grepcheck(
                self, '/proc/1/environ', 'container=lxc')
            # detect wsl
            kc_wsl = KCFileUtils.grepcheck(
                self, '/proc/1/environ', 'wsl')
        else:
            kc_wsl = True
            kc_lxc = True

        if (kc_lxc is not True) and (kc_wsl is not True) and (kc_arch is True):
            data = dict()
            KCTemplate.deploy(
                self, '/etc/sysctl.d/60-kc-tweaks.conf',
                'sysctl.mustache', data, True)
            # use tcp_bbr congestion algorithm only on new kernels
            if (KCVar.kc_platform_codename == 'bionic' or
                KCVar.kc_platform_codename == 'focal' or
                    KCVar.kc_platform_codename == 'buster'):
                try:
                    KCShellExec.cmd_exec(
                        self, 'modprobe tcp_bbr')
                    with open(
                        "/etc/modules-load.d/bbr.conf",
                            encoding='utf-8', mode='w') as bbr_file:
                        bbr_file.write('tcp_bbr')
                    with open(
                        "/etc/sysctl.d/60-kc-tweaks.conf",
                            encoding='utf-8', mode='a') as sysctl_file:
                        sysctl_file.write(
                            '\nnet.ipv4.tcp_congestion_control = bbr'
                            '\nnet.ipv4.tcp_notsent_lowat = 16384')
                except OSError as e:
                    Log.debug(self, str(e))
                    Log.warn(self, "failed to tweak sysctl")
            else:
                try:
                    KCShellExec.cmd_exec(
                        self, 'modprobe tcp_htcp')
                    with open(
                        "/etc/modules-load.d/htcp.conf",
                            encoding='utf-8', mode='w') as bbr_file:
                        bbr_file.write('tcp_htcp')
                    with open(
                        "/etc/sysctl.d/60-kc-tweaks.conf",
                            encoding='utf-8', mode='a') as sysctl_file:
                        sysctl_file.write(
                            '\nnet.ipv4.tcp_congestion_control = htcp')
                except OSError as e:
                    Log.debug(self, str(e))
                    Log.warn(self, "failed to tweak sysctl")

            # apply sysctl tweaks
            KCShellExec.cmd_exec(
                self, 'sysctl -eq -p /etc/sysctl.d/60-kc-tweaks.conf')

        # sysctl tweak service
        data = dict()
        if not os.path.isfile('/opt/kc-kernel.sh'):
            KCTemplate.deploy(self, '/opt/kc-kernel.sh',
                              'kc-kernel-script.mustache', data)
        KCFileUtils.chmod(self, '/opt/kc-kernel.sh', 0o700)
        if not os.path.isfile('/lib/systemd/system/kc-kernel.service'):
            KCTemplate.deploy(
                self, '/lib/systemd/system/kc-kernel.service',
                'kc-kernel-service.mustache', data)
            KCShellExec.cmd_exec(self, 'systemctl enable kc-kernel.service')
            KCService.start_service(self, 'kc-kernel')
        # open_files_limit tweak
        if not KCFileUtils.grepcheck(self,
                                     '/etc/security/limits.conf', '500000'):
            with open("/etc/security/limits.conf",
                      encoding='utf-8', mode='a') as limit_file:
                limit_file.write(
                    '*         hard    nofile      500000\n'
                    '*         soft    nofile      500000\n'
                    'root      hard    nofile      500000\n'
                    'root      soft    nofile      500000\n')
        # custom motd-news
        data = dict()
        # check if update-motd.d directory exist
        if os.path.isdir('/etc/update-motd.d/'):
            # render custom motd template
            KCTemplate.deploy(
                self, '/etc/update-motd.d/98-kc-update',
                'kc-update.mustache', data)
            KCFileUtils.chmod(
                self, "/etc/update-motd.d/98-kc-update", 0o755)
        with open('/var/lib/kc/version.txt',
                  mode='w', encoding='utf-8') as kc_ver:
            kc_ver.write('{0}'.format(KCVar.kc_version))
