import requests

from kc.core.shellexec import KCShellExec
from kc.core.variables import KCVar


def check_fqdn(self, kc_host):
    """FQDN check with KeepCloud, for mail server hostname must be FQDN"""
    # kc_host=os.popen("hostname -f | tr -d '\n'").read()
    if '.' in kc_host:
        KCVar.kc_fqdn = kc_host
        with open('/etc/hostname', encoding='utf-8', mode='w') as hostfile:
            hostfile.write(kc_host)

        KCShellExec.cmd_exec(self, "sed -i \"1i\\127.0.0.1 {0}\" /etc/hosts"
                                   .format(kc_host))
        if KCVar.kc_distro == 'debian':
            KCShellExec.cmd_exec(self, "/etc/init.d/hostname.sh start")
        else:
            KCShellExec.cmd_exec(self, "service hostname restart")

    else:
        kc_host = input("Enter hostname [fqdn]:")
        check_fqdn(self, kc_host)


def check_fqdn_ip(self):
    """Check if server hostname resolved server IP"""
    x = requests.get('http://v4.wordops.eu')
    ip = (x.text).strip()

    kc_fqdn = KCVar.kc_fqdn
    y = requests.get('http://v4.wordops.eu/dns/{0}/'.format(kc_fqdn))
    ip_fqdn = (y.text).strip()

    return bool(ip == ip_fqdn)
