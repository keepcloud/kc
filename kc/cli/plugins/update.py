import os
import time


from cement.core.controller import CementBaseController, expose
from kc.core.download import KCDownload
from kc.core.logging import Log
from kc.core.variables import KCVar


def kc_update_hook(app):
    pass


class KCUpdateController(CementBaseController):
    class Meta:
        label = 'kc_update'
        stacked_on = 'base'
        aliases = ['update']
        aliases_only = True
        stacked_type = 'nested'
        description = ('update KeepCloud to latest version')
        arguments = [
            (['--force'],
             dict(help='Force KeepCloud update', action='store_true')),
            (['--beta'],
             dict(help='Update KeepCloud to latest mainline release '
                  '(same than --mainline)',
                  action='store_true')),
            (['--mainline'],
             dict(help='Update KeepCloud to latest mainline release',
                  action='store_true')),
            (['--branch'],
                dict(help="Update KeepCloud from a specific repository branch ",
                     action='store' or 'store_const',
                     const='develop', nargs='?')),
            (['--travis'],
             dict(help='Argument used only for KeepCloud development',
                  action='store_true')),
        ]
        usage = "kc update [options]"

    @expose(hide=True)
    def default(self):
        pargs = self.app.pargs
        filename = "kcupdate" + time.strftime("%Y%m%d-%H%M%S")

        install_args = ""
        kc_branch = "master"
        if pargs.mainline or pargs.beta:
            kc_branch = "mainline"
            install_args = install_args + "--mainline "
        elif pargs.branch:
            kc_branch = pargs.branch
            install_args = install_args + "-b {0} ".format(kc_branch)
        if pargs.force:
            install_args = install_args + "--force "
        if pargs.travis:
            install_args = install_args + "--travis "
            kc_branch = "updating-configuration"

        if ((not pargs.force) and (not pargs.travis) and
            (not pargs.mainline) and (not pargs.beta) and
                (not pargs.branch)):
            kc_current = ("v{0}".format(KCVar.kc_version))
            kc_latest = KCDownload.latest_release(self, "KeepCloud/kc")
            if kc_current == kc_latest:
                Log.info(
                    self, "KeepCloud {0} is already installed"
                    .format(kc_latest))
                self.app.close(0)

        if not os.path.isdir('/var/lib/kc/tmp'):
            os.makedirs('/var/lib/kc/tmp')
        KCDownload.download(self, [["https://raw.githubusercontent.com/"
                                    "KeepCloud/kc/{0}/install"
                                    .format(kc_branch),
                                    "/var/lib/kc/tmp/{0}".format(filename),
                                    "update script"]])

        if os.path.isfile('install'):
            Log.info(self, "updating KeepCloud from local install\n")
            try:
                Log.info(self, "updating KeepCloud, please wait...")
                os.system("/bin/bash install --travis")
            except OSError as e:
                Log.debug(self, str(e))
                Log.error(self, "KeepCloud update failed !")
        else:
            try:
                Log.info(self, "updating KeepCloud, please wait...")
                os.system("/bin/bash /var/lib/kc/tmp/{0} "
                          "{1}".format(filename, install_args))
            except OSError as e:
                Log.debug(self, str(e))
                Log.error(self, "KeepCloud update failed !")

        os.remove("/var/lib/kc/tmp/{0}".format(filename))


def load(app):
    # register the plugin class.. this only happens if the plugin is enabled
    app.handler.register(KCUpdateController)
    # register a hook (function) to run after arguments are parsed.
    app.hook.register('post_argument_parsing', kc_update_hook)
