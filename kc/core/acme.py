import csv
import os

import requests

from kc.core.fileutils import KCFileUtils
from kc.core.git import KCGit
from kc.core.logging import Log
from kc.core.shellexec import KCShellExec, CommandExecutionError
from kc.core.variables import KCVar


class KCAcme:
    """Acme.sh utilities for WordOps"""

    kc_acme_exec = ("/etc/letsencrypt/acme.sh --config-home "
                    "'/etc/letsencrypt/config'")

    def check_acme(self):
        """
        Check if acme.sh is properly installed,
        and install it if required
        """
        if not os.path.exists('/etc/letsencrypt/acme.sh'):
            if os.path.exists('/opt/acme.sh'):
                KCFileUtils.rm(self, '/opt/acme.sh')
            KCGit.clone(
                self, 'https://github.com/Neilpang/acme.sh.git',
                '/opt/acme.sh', branch='master')
            KCFileUtils.mkdir(self, '/etc/letsencrypt/config')
            KCFileUtils.mkdir(self, '/etc/letsencrypt/renewal')
            KCFileUtils.mkdir(self, '/etc/letsencrypt/live')
            try:
                KCFileUtils.chdir(self, '/opt/acme.sh')
                KCShellExec.cmd_exec(
                    self, './acme.sh --install --home /etc/letsencrypt'
                    '--config-home /etc/letsencrypt/config'
                    '--cert-home /etc/letsencrypt/renewal'
                )
                KCShellExec.cmd_exec(
                    self, "{0} --upgrade --auto-upgrade"
                    .format(KCAcme.wo_acme_exec)
                )
            except CommandExecutionError as e:
                Log.debug(self, str(e))
                Log.error(self, "acme.sh installation failed")
        if not os.path.exists('/etc/letsencrypt/acme.sh'):
            Log.error(self, 'acme.sh ')

    def export_cert(self):
        """Export acme.sh csv certificate list"""
        # check acme.sh is installed
        KCAcme.check_acme(self)
        acme_list = KCShellExec.cmd_exec_stdout(
            self, "{0} ".format(KCAcme.wo_acme_exec) +
            "--list --listraw")
        if acme_list:
            KCFileUtils.textwrite(self, '/var/lib/wo/cert.csv', acme_list)
            KCFileUtils.chmod(self, '/var/lib/wo/cert.csv', 0o600)
        else:
            Log.error(self, "Unable to export certs list")

    def setupletsencrypt(self, acme_domains, acmedata):
        """Issue SSL certificates with acme.sh"""
        # check acme.sh is installed
        KCAcme.check_acme(self)
        # define variables
        all_domains = '\' -d \''.join(acme_domains)
        wo_acme_dns = acmedata['acme_dns']
        keylenght = acmedata['keylength']
        if acmedata['dns'] is True:
            acme_mode = "--dns {0}".format(wo_acme_dns)
            validation_mode = "DNS mode with {0}".format(wo_acme_dns)
            if acmedata['dnsalias'] is True:
                acme_mode = acme_mode + \
                    " --challenge-alias {0}".format(acmedata['acme_alias'])
        else:
            acme_mode = "-w /var/www/html"
            validation_mode = "Webroot challenge"
            Log.debug(self, "Validation : Webroot mode")
            if not os.path.isdir('/var/www/html/.well-known/acme-challenge'):
                KCFileUtils.mkdir(
                    self, '/var/www/html/.well-known/acme-challenge')
            KCFileUtils.chown(
                self, '/var/www/html/.well-known', 'www-data', 'www-data',
                recursive=True)
            KCFileUtils.chmod(self, '/var/www/html/.well-known', 0o750,
                              recursive=True)

        Log.info(self, "Validation mode : {0}".format(validation_mode))
        Log.wait(self, "Issuing SSL cert with acme.sh")
        if not KCShellExec.cmd_exec(
                self, "{0} ".format(KCAcme.wo_acme_exec) +
                "--issue -d '{0}' {1} -k {2} -f"
                .format(all_domains, acme_mode, keylenght)):
            Log.failed(self, "Issuing SSL cert with acme.sh")
            if acmedata['dns'] is True:
                Log.error(
                    self, "Please make sure your properly "
                    "set your DNS API credentials for acme.sh\n"
                    "If you are using sudo, use \"sudo -E wo\"")
                return False
            else:
                Log.error(
                    self, "Your domain is properly configured "
                    "but acme.sh was unable to issue certificate.\n"
                    "You can find more informations in "
                    "/var/log/kc/keepcloud.log")
                return False
        else:
            Log.valide(self, "Issuing SSL cert with acme.sh")
            return True

    def deploycert(self, kc_domain_name):
        """Deploy Let's Encrypt certificates with acme.sh"""
        # check acme.sh is installed
        KCAcme.check_acme(self)
        if not os.path.isfile('/etc/letsencrypt/renewal/{0}_ecc/fullchain.cer'
                              .format(kc_domain_name)):
            Log.error(self, 'Certificate not found. Deployment canceled')

        Log.debug(self, "Cert deployment for domain: {0}"
                  .format(kc_domain_name))

        try:
            Log.wait(self, "Deploying SSL cert")
            if KCShellExec.cmd_exec(
                self, "mkdir -p {0}/{1} && {2} --install-cert -d {1} --ecc "
                "--cert-file {0}/{1}/cert.pem --key-file {0}/{1}/key.pem "
                "--fullchain-file {0}/{1}/fullchain.pem "
                "--ca-file {0}/{1}/ca.pem --reloadcmd \"nginx -t && "
                "service nginx restart\" "
                .format(KCVar.wo_ssl_live,
                        kc_domain_name, KCAcme.kc_acme_exec)):
                Log.valide(self, "Deploying SSL cert")
            else:
                Log.failed(self, "Deploying SSL cert")
                Log.error(self, "Unable to deploy certificate")

            if os.path.isdir('/var/www/{0}/conf/nginx'
                             .format(kc_domain_name)):

                sslconf = open("/var/www/{0}/conf/nginx/ssl.conf"
                               .format(kc_domain_name),
                               encoding='utf-8', mode='w')
                sslconf.write(
                    "listen 443 ssl http2;\n"
                    "listen [::]:443 ssl http2;\n"
                    "ssl_certificate     {0}/{1}/fullchain.pem;\n"
                    "ssl_certificate_key     {0}/{1}/key.pem;\n"
                    "ssl_trusted_certificate {0}/{1}/ca.pem;\n"
                    "ssl_stapling_verify on;\n"
                    .format(KCVar.wo_ssl_live, kc_domain_name))
                sslconf.close()

            if not KCFileUtils.grep(self, '/var/www/22222/conf/nginx/ssl.conf',
                                    '/etc/letsencrypt'):
                Log.info(self, "Securing WordOps backend with current cert")
                sslconf = open("/var/www/22222/conf/nginx/ssl.conf",
                               encoding='utf-8', mode='w')
                sslconf.write("ssl_certificate     {0}/{1}/fullchain.pem;\n"
                              "ssl_certificate_key     {0}/{1}/key.pem;\n"
                              "ssl_trusted_certificate {0}/{1}/ca.pem;\n"
                              "ssl_stapling_verify on;\n"
                              .format(KCVar.wo_ssl_live, kc_domain_name))
                sslconf.close()

            KCGit.add(self, ["/etc/letsencrypt"],
                      msg="Adding letsencrypt folder")

        except IOError as e:
            Log.debug(self, str(e))
            Log.debug(self, "Error occured while generating "
                      "ssl.conf")
        return 0

    def renew(self, domain):
        """Renew letsencrypt certificate with acme.sh"""
        # check acme.sh is installed
        KCAcme.check_acme(self)
        try:
            KCShellExec.cmd_exec(
                self, "{0} ".format(KCAcme.wo_acme_exec) +
                "--renew -d {0} --ecc --force".format(domain))
        except CommandExecutionError as e:
            Log.debug(self, str(e))
            Log.error(self, 'Unable to renew certificate')
        return True

    def check_dns(self, acme_domains):
        """Check if a list of domains point to the server IP"""
        server_ip = requests.get('https://v4.wordops.eu/').text
        for domain in acme_domains:
            domain_ip = requests.get('http://v4.wordops.eu/dns/{0}/'
                                     .format(domain)).text
            if(not domain_ip == server_ip):
                Log.warn(
                    self, "{0}".format(domain) +
                    " point to the IP {0}".format(domain_ip) +
                    " but your server IP is {0}.".format(server_ip) +
                    "\nUse the flag --force to bypass this check.")
                Log.error(
                    self, "You have to set the "
                    "proper DNS record for your domain", False)
                return False
        Log.debug(self, "DNS record are properly set")
        return True

    def cert_check(self, kc_domain_name):
        """Check certificate existance with acme.sh and return Boolean"""
        KCAcme.export_cert(self)
        # set variable acme_cert
        acme_cert = False
        # define new csv dialect
        csv.register_dialect('acmeconf', delimiter='|')
        # open file
        certfile = open('/var/lib/kc/cert.csv',
                        mode='r', encoding='utf-8')
        reader = csv.reader(certfile, 'acmeconf')
        for row in reader:
            # check if domain exist
            if kc_domain_name == row[0]:
                # check if cert expiration exist
                if not row[3] == '':
                    acme_cert = True
        certfile.close()
        if acme_cert is True:
            if os.path.exists(
                '/etc/letsencrypt/live/{0}/fullchain.pem'
                    .format(kc_domain_name)):
                return True
        return False

    def removeconf(self, domain):
        sslconf = ("/var/www/{0}/conf/nginx/ssl.conf"
                   .format(domain))
        sslforce = ("/etc/nginx/conf.d/force-ssl-{0}.conf"
                    .format(domain))
        acmedir = [
            '{0}'.format(sslforce), '{0}'.format(sslconf),
            '{0}/{1}_ecc'.format(KCVar.wo_ssl_archive, domain),
            '{0}.disabled'.format(sslconf), '{0}.disabled'
            .format(sslforce), '{0}/{1}'
            .format(KCVar.wo_ssl_live, domain),
            '/etc/letsencrypt/shared/{0}.conf'.format(domain)]
        kc_domain = domain
        # check acme.sh is installed
        KCAcme.check_acme(self)
        if KCAcme.cert_check(self, kc_domain):
            Log.info(self, "Removing Acme configuration")
            Log.debug(self, "Removing Acme configuration")
            try:
                KCShellExec.cmd_exec(
                    self, "{0} ".format(KCAcme.kc_acme_exec) +
                    "--remove -d {0} --ecc".format(domain))
            except CommandExecutionError as e:
                Log.debug(self, "{0}".format(e))
                Log.error(self, "Cert removal failed")
            # remove all files and directories
            for dir in acmedir:
                if os.path.exists('{0}'.format(dir)):
                    KCFileUtils.rm(self, '{0}'.format(dir))
            # find all broken symlinks
            KCFileUtils.findBrokenSymlink(self, "/var/www")
        else:
            if os.path.islink("{0}".format(sslconf)):
                KCFileUtils.remove_symlink(self, "{0}".format(sslconf))
                KCFileUtils.rm(self, '{0}'.format(sslforce))

        if KCFileUtils.grepcheck(self, '/var/www/22222/conf/nginx/ssl.conf',
                                 '{0}'.format(domain)):
            Log.info(
                self, "Setting back default certificate for KeepCloud backend")
            with open("/var/www/22222/conf/nginx/"
                      "ssl.conf", "w") as ssl_conf_file:
                ssl_conf_file.write("ssl_certificate "
                                    "/var/www/22222/cert/22222.crt;\n"
                                    "ssl_certificate_key "
                                    "/var/www/22222/cert/22222.key;\n")
