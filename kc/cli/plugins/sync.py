import glob
import os

from cement.core.controller import CementBaseController, expose

from kc.cli.plugins.sitedb import getAllsites, updateSiteInfo
from kc.core.fileutils import KCFileUtils
from kc.core.logging import Log
from kc.core.mysql import StatementExcecutionError, KCMysql


def kc_sync_hook(app):
    pass


class KCSyncController(CementBaseController):
    class Meta:
        label = 'sync'
        stacked_on = 'base'
        stacked_type = 'nested'
        description = 'synchronize the KeepCloud database'

    @expose(hide=True)
    def default(self):
        self.sync()

    @expose(hide=True)
    def sync(self):
        """
        1. reads database information from wp/kc-config.php
        2. updates records into kc database accordingly.
        """
        Log.info(self, "Synchronizing kc database, please wait...")
        sites = getAllsites(self)
        if not sites:
            pass
        for site in sites:
            if site.site_type in ['mysql', 'wp', 'wpsubdir', 'wpsubdomain']:
                kc_site_webroot = site.site_path
                # Read config files
                configfiles = glob.glob(kc_site_webroot + '/*-config.php')

                if (os.path.exists(
                    '{0}/ee-config.php'.format(kc_site_webroot)) and
                    os.path.exists(
                        '{0}/kc-config.php'.format(kc_site_webroot))):
                    configfiles = glob.glob(
                        kc_site_webroot + 'kc-config.php')

                # search for wp-config.php inside htdocs/
                if not configfiles:
                    Log.debug(self, "Config files not found in {0}/ "
                                    .format(kc_site_webroot))
                    if site.site_type != 'mysql':
                        Log.debug(self,
                                  "Searching wp-config.php in {0}/htdocs/"
                                  .format(kc_site_webroot))
                        configfiles = glob.glob(
                            kc_site_webroot + '/htdocs/wp-config.php')

                if configfiles:
                    if KCFileUtils.isexist(self, configfiles[0]):
                        kc_db_name = (
                            KCFileUtils.grep(self, configfiles[0],
                                             'DB_NAME').split(',')[1]
                            .split(')')[0].strip().replace('\'', ''))
                        kc_db_user = (
                            KCFileUtils.grep(self, configfiles[0],
                                             'DB_USER').split(',')[1]
                            .split(')')[0].strip().replace('\'', ''))
                        kc_db_pass = (
                            KCFileUtils.grep(self, configfiles[0],
                                             'DB_PASSWORD').split(',')[1]
                            .split(')')[0].strip().replace('\'', ''))
                        kc_db_host = (
                            KCFileUtils.grep(self, configfiles[0],
                                             'DB_HOST').split(',')[1]
                            .split(')')[0].strip().replace('\'', ''))

                        # Check if database really exist
                        try:
                            if not KCMysql.check_db_exists(self, kc_db_name):
                                # Mark it as deleted if not exist
                                kc_db_name = 'deleted'
                                kc_db_user = 'deleted'
                                kc_db_pass = 'deleted'
                        except StatementExcecutionError as e:
                            Log.debug(self, str(e))
                        except Exception as e:
                            Log.debug(self, str(e))

                        if site.db_name != kc_db_name:
                            # update records if any mismatch found
                            Log.debug(self, "Updating kc db record for {0}"
                                      .format(site.sitename))
                            updateSiteInfo(self, site.sitename,
                                           db_name=kc_db_name,
                                           db_user=kc_db_user,
                                           db_password=kc_db_pass,
                                           db_host=kc_db_host)
                else:
                    Log.debug(self, "Config files not found for {0} "
                              .format(site.sitename))


def load(app):
    # register the plugin class.. this only happens if the plugin is enabled
    app.handler.register(KCSyncController)
    # register a hook (function) to run after arguments are parsed.
    app.hook.register('post_argument_parsing', kc_sync_hook)
