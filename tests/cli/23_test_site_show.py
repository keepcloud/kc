from kc.utils import test
from kc.cli.main import KCTestApp


class CliTestCaseSiteShow(test.KCTestCase):

    def test_kc_cli_show_edit(self):
        with KCTestApp(argv=['site', 'show', 'html.com']) as app:
            app.run()
