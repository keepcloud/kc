import os

from kc.core.logging import Log
from kc.core.template import KCTemplate
from kc.core.variables import KCVar


class KCConf():
    """kc stack configuration utilities"""
    def __init__():
        pass

    def nginxcommon(self):
        """nginx common configuration deployment"""
        kc_php_version = ["php72", "php73", "php74", "php80", "php81"]
        ngxcom = '/etc/nginx/common'
        if not os.path.exists(ngxcom):
            os.mkdir(ngxcom)
        for kc_php in kc_php_version:
            Log.debug(self, 'deploying templates for {0}'.format(kc_php))
            data = dict(upstream="{0}".format(kc_php),
                        release=KCVar.kc_version)
            KCTemplate.deploy(self,
                              '{0}/{1}.conf'
                              .format(ngxcom, kc_php),
                              'php.mustache', data)

            KCTemplate.deploy(
                self, '{0}/redis-{1}.conf'.format(ngxcom, kc_php),
                'redis.mustache', data)

            KCTemplate.deploy(
                self, '{0}/wpcommon-{1}.conf'.format(ngxcom, kc_php),
                'wpcommon.mustache', data)

            KCTemplate.deploy(
                self, '{0}/wpfc-{1}.conf'.format(ngxcom, kc_php),
                'wpfc.mustache', data)

            KCTemplate.deploy(
                self, '{0}/wpsc-{1}.conf'.format(ngxcom, kc_php),
                'wpsc.mustache', data)

            KCTemplate.deploy(
                self, '{0}/wprocket-{1}.conf'.format(ngxcom, kc_php),
                'wprocket.mustache', data)

            KCTemplate.deploy(
                self, '{0}/wpce-{1}.conf'.format(ngxcom, kc_php),
                'wpce.mustache', data)
