"""Keepcloud Swap Creation"""
import os

import psutil

from kc.core.aptget import KCAptGet
from kc.core.fileutils import KCFileUtils
from kc.core.logging import Log
from kc.core.shellexec import KCShellExec


class KCSwap():
    """Manage Swap"""

    def __init__():
        """Initialize """
        pass

    def add(self):
        """Swap addition with KeepCloud"""
        # Get System RAM and SWAP details
        kc_ram = psutil.virtual_memory().total / (1024 * 1024)
        kc_swap = psutil.swap_memory().total / (1024 * 1024)
        if kc_ram < 512:
            if kc_swap < 1000:
                Log.info(self, "Adding SWAP file, please wait...")

                # Install dphys-swapfile
                KCAptGet.update(self)
                KCAptGet.install(self, ["dphys-swapfile"])
                # Stop service
                KCShellExec.cmd_exec(self, "service dphys-swapfile stop")
                # Remove Default swap created
                KCShellExec.cmd_exec(self, "/sbin/dphys-swapfile uninstall")

                # Modify Swap configuration
                if os.path.isfile("/etc/dphys-swapfile"):
                    KCFileUtils.searchreplace(self, "/etc/dphys-swapfile",
                                              "#CONF_SWAPFILE=/var/swap",
                                              "CONF_SWAPFILE=/kc-swapfile")
                    KCFileUtils.searchreplace(self, "/etc/dphys-swapfile",
                                              "#CONF_MAXSWAP=2048",
                                              "CONF_MAXSWAP=1024")
                    KCFileUtils.searchreplace(self, "/etc/dphys-swapfile",
                                              "#CONF_SWAPSIZE=",
                                              "CONF_SWAPSIZE=1024")
                else:
                    with open("/etc/dphys-swapfile", 'w') as conffile:
                        conffile.write("CONF_SWAPFILE=/kc-swapfile\n"
                                       "CONF_SWAPSIZE=1024\n"
                                       "CONF_MAXSWAP=1024\n")
                # Create swap file
                KCShellExec.cmd_exec(self, "service dphys-swapfile start")
