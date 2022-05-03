from kc.utils import test
from kc.cli.main import KCTestApp


class CliTestCaseSiteEnable(test.KCTestCase):

    def test_kc_cli_site_enable(self):
        with KCTestApp(argv=['site', 'enable', 'html.com']) as app:
            app.run()
