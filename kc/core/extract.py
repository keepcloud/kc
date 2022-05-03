"""KeepCloud Extract Core """
import os
import tarfile

from kc.core.logging import Log


class KCExtract():
    """Method to extract from tar.gz file"""

    def extract(self, file, path):
        """Function to extract tar.gz file"""
        try:
            tar = tarfile.open(file)
            tar.extractall(path=path)
            tar.close()
            os.remove(file)
            return True
        except tarfile.TarError as e:
            Log.debug(self, "{0}".format(e))
            Log.error(self, 'Unable to extract file \{0}'.format(file))
            return False
