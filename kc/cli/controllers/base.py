"""KeepCloud base controller."""

from cement.core.controller import CementBaseController, expose

from kc.core.variables import KCVar

VERSION = KCVar.kc_version

BANNER = """
KeepCloud v%s
Copyright (c) 2022 KeepCloud.
""" % VERSION


class KCBaseController(CementBaseController):
    class Meta:
        label = 'base'
        description = ("An essential toolset that eases KeepCloud "
                       "site and server administration with Nginx")
        arguments = [
            (['-v', '--version'], dict(action='version', version=BANNER)),
        ]

    @expose(hide=True)
    def default(self):
        self.app.args.print_help()
