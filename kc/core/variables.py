"""KeepCloud core variable module"""
import configparser
import os
from datetime import datetime
from re import match
from socket import getfqdn
from shutil import copy2

from distro import linux_distribution
from sh import git


class KCVar():
    """Intialization of core variables"""

    # KeepCloud version
    kc_version = "1.0"
    # KeepCloud packages versions
    kc_wp_cli = "2.6.0"
    kc_adminer = "4.8.1"
    kc_phpmyadmin = "5.0.2"
    kc_extplorer = "2.1.13"
    kc_dashboard = "1.2"

    # Get WPCLI path
    kc_wpcli_path = '/usr/local/bin/wp'

    # Current date and time of System
    kc_date = datetime.now().strftime('%d%b%Y-%H-%M-%S')

    # Keepcloud core variables
    # linux distribution
    kc_distro = linux_distribution(
        full_distribution_name=False)[0].lower()
    kc_platform_version = linux_distribution(
        full_distribution_name=False)[1].lower()
    # distro codename (bionic, xenial, stretch ...)
    kc_platform_codename = linux_distribution(
        full_distribution_name=False)[2].lower()

    # Get timezone of system
    if os.path.isfile('/etc/timezone'):
        with open("/etc/timezone", mode='r', encoding='utf-8') as tzfile:
            kc_timezone = tzfile.read().replace('\n', '')
            if kc_timezone == "Etc/UTC":
                kc_timezone = "UTC"
    else:
        kc_timezone = "America/Fortaleza"

    # Get FQDN of system
    kc_fqdn = getfqdn()

    # Keepcloud default webroot path
    kc_webroot = '/var/www/'

    # Keepcloud default renewal  SSL certificates path
    kc_ssl_archive = '/etc/letsencrypt/renewal'

    # Keepcloud default live SSL certificates path
    kc_ssl_live = '/etc/letsencrypt/live'

    # PHP user
    kc_php_user = 'www-data'

    # Keepcloud git configuration management
    config = configparser.ConfigParser()
    config.read(os.path.expanduser("~") + '/.gitconfig')
    try:
        kc_user = config['user']['name']
        kc_email = config['user']['email']
    except Exception:
        print("Keepcloud (kc) require an username & and an email "
              "address to configure Git (used to save server configurations)")
        print("Your informations will ONLY be stored locally")

        kc_user = input("Enter your name: ")
        while kc_user == "":
            print("Unfortunately, this can't be left blank")
            kc_user = input("Enter your name: ")

        kc_email = input("Enter your email: ")

        while not match(r"^[A-Za-z0-9\.\+_-]+@[A-Za-z0-9\._-]+\.[a-zA-Z]*$",
                        kc_email):
            print("Whoops, seems like you made a typo - "
                  "the e-mail address is invalid...")
            kc_email = input("Enter your email: ")

        git.config("--global", "user.name", "{0}".format(kc_user))
        git.config("--global", "user.email", "{0}".format(kc_email))

    if not os.path.isfile('/root/.gitconfig'):
        copy2(os.path.expanduser("~") + '/.gitconfig', '/root/.gitconfig')

    # MySQL hostname
    kc_mysql_host = ""
    config = configparser.RawConfigParser()
    if os.path.exists('/etc/mysql/conf.d/my.cnf'):
        cnfpath = "/etc/mysql/conf.d/my.cnf"
    else:
        cnfpath = os.path.expanduser("~") + "/.my.cnf"
    if [cnfpath] == config.read(cnfpath):
        try:
            kc_mysql_host = config.get('client', 'host')
        except configparser.NoOptionError:
            kc_mysql_host = "localhost"
    else:
        kc_mysql_host = "localhost"

    # Keepcloud stack installation variables
    # Nginx repo and packages
    if kc_distro == 'ubuntu':
        kc_nginx_repo = "ppa:wordops/nginx-wo"
        kc_extra_repo = (
            "deb http://download.opensuse.org"
            "/repositories/home:/virtubox:"
            "/WordOps/xUbuntu_{0}/ /".format(kc_platform_version))
    else:
        if kc_distro == 'debian':
            if kc_platform_codename == 'jessie':
                kc_deb_repo = "Debian_8.0"
            elif kc_platform_codename == 'stretch':
                kc_deb_repo = "Debian_9.0"
            elif kc_platform_codename == 'buster':
                kc_deb_repo = "Debian_10"
        elif kc_distro == 'raspbian':
            if kc_platform_codename == 'stretch':
                kc_deb_repo = "Raspbian_9.0"
            elif kc_platform_codename == 'buster':
                kc_deb_repo = "Raspbian_10"
        # debian/raspbian nginx repository
        kc_nginx_repo = ("deb http://download.opensuse.org"
                         "/repositories/home:"
                         "/virtubox:/WordOps/{0}/ /"
                         .format(kc_deb_repo))

    kc_nginx = ["nginx-custom", "nginx-wo"]
    kc_nginx_key = '188C9FB063F0247A'

    kc_module = ["bcmath", "cli", "common", "curl", "fpm", "gd", "igbinary",
                 "imagick", "imap", "intl", "mbstring", "memcached", "msgpack",
                 "mysql", "opcache", "readline", "redis", "soap", "xdebug",
                 "xml", "zip"]
    kc_php72 = []
    for module in kc_module:
        kc_php72 = kc_php72 + ["php7.2-{0}".format(module)]
    kc_php72 = kc_php72 + ["php7.2-recode"]
    kc_php73 = []
    for module in kc_module:
        kc_php73 = kc_php73 + ["php7.3-{0}".format(module)]
    kc_php73 = kc_php73 + ["php7.3-recode"]
    kc_php74 = []
    for module in kc_module:
        kc_php74 = kc_php74 + ["php7.4-{0}".format(module)]
    kc_php74 = kc_php74 + ["php7.4-geoip", "php7.4-json"]
    kc_php80 = []
    for module in kc_module:
        kc_php80 = kc_php80 + ["php8.0-{0}".format(module)]
    kc_php81 = []
    for module in kc_module:
        kc_php81 = kc_php81 + ["php8.1-{0}".format(module)]

    kc_php_extra = ["graphviz"]

    kc_mysql = [
        "mariadb-server", "percona-toolkit",
        "mariadb-common", "python3-mysqldb"]
    if kc_distro == 'raspbian':
        if kc_platform_codename == 'stretch':
            mariadb_ver = '10.1'
        else:
            mariadb_ver = '10.3'
    else:
        mariadb_ver = '10.5'
        kc_mysql = kc_mysql + ["mariadb-backup"]

    kc_mysql_client = ["mariadb-client", "python3-mysqldb"]

    kc_fail2ban = ["fail2ban"]
    kc_clamav = ["clamav", "clamav-freshclam"]
    kc_ubuntu_backports = 'ppa:jonathonf/backports'

    # APT repositories
    kc_mysql_repo = ("deb [arch=amd64,arm64,ppc64el] "
                     "http://mariadb.mirrors.ovh.net/MariaDB/repo/"
                     "10.5/{distro} {codename} main"
                     .format(distro=kc_distro,
                             codename=kc_platform_codename))
    if kc_distro == 'ubuntu':
        kc_php_repo = "ppa:ondrej/php"
        kc_redis_repo = ("ppa:redislabs/redis")
        kc_goaccess_repo = ("ppa:alex-p/goaccess")

    else:
        kc_php_repo = (
            "deb https://packages.sury.org/php/ {codename} main"
            .format(codename=kc_platform_codename))
        kc_php_key = 'AC0E47584A7A714D'
        kc_redis_repo = ("deb https://packages.sury.org/php/ {codename} all"
                         .format(codename=kc_platform_codename))

    kc_redis = ['redis-server']

    # Repo path
    kc_repo_file = "kc-repo.list"
    kc_repo_file_path = ("/etc/apt/sources.list.d/" + kc_repo_file)

    # Application dabase file path
    basedir = os.path.abspath(os.path.dirname('/var/lib/kc/'))
    kc_db_uri = 'sqlite:///' + os.path.join(basedir, 'dbase.db')

    def __init__(self):
        pass
