from kc.utils import test
from kc.cli.main import KCTestApp


class CliTestCaseInfo(test.KCTestCase):

    def test_kc_cli_info_mysql(self):
        with KCTestApp(argv=['info', '--mysql']) as app:
            app.run()

    def test_kc_cli_info_php(self):
        with KCTestApp(argv=['info', '--php']) as app:
            app.run()

    def test_kc_cli_info_nginx(self):
        with KCTestApp(argv=['info', '--nginx']) as app:
            app.run()
