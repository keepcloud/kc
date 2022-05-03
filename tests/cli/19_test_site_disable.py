from kc.utils import test
from kc.cli.main import KCTestApp


class CliTestCaseSiteDisable(test.KCTestCase):

    def test_kc_cli_site_disable(self):
        with KCTestApp(argv=['site', 'disable', 'html.com']) as app:
            app.run()
