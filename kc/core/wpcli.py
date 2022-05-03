"""Keepcloud utilities for WordOps"""
from kc.core.logging import Log
from kc.core.shellexec import KCShellExec
from kc.core.variables import KCVar


class KCWp:
    """Keepcloud utilities for WordOps"""

    def wpcli(self, command):
        """WP-CLI wrapper"""
        try:
            KCShellExec.cmd_exec(
                self, '{0} --allow-root '.format(KCVar.kc_wpcli_path) +
                '{0}'.format(command))
        except Exception:
            Log.error(self, "WP-CLI command failed")
