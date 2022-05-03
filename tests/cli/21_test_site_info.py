from kc.utils import test
from kc.cli.main import KCTestApp


class CliTestCaseSiteInfo(test.KCTestCase):

    def test_kc_cli_site_info(self):
        with KCTestApp(argv=['site', 'info', 'html.com']) as app:
            app.run()
