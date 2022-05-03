from kc.utils import test
from kc.cli.main import KCTestApp


class CliTestCaseSiteList(test.KCTestCase):

    def test_kc_cli_site_list_enable(self):
        with KCTestApp(argv=['site', 'list', '--enabled']) as app:
            app.run()

    def test_kc_cli_site_list_disable(self):
        with KCTestApp(argv=['site', 'list', '--disabled']) as app:
            app.run()
