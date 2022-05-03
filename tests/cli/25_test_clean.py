from kc.utils import test
from kc.cli.main import KCTestApp


class CliTestCaseClean(test.KCTestCase):

    def test_kc_cli_clean(self):
        with KCTestApp(argv=['clean']) as app:
            app.run()

    def test_kc_cli_clean_fastcgi(self):
        with KCTestApp(argv=['clean', '--fastcgi']) as app:
            app.run()

    def test_kc_cli_clean_all(self):
        with KCTestApp(argv=['clean', '--all']) as app:
            app.run()

    def test_kc_cli_clean_opcache(self):
        with KCTestApp(argv=['clean', '--opcache']) as app:
            app.run()

    def test_kc_cli_clean_redis(self):
        with KCTestApp(argv=['clean', '--redis']) as app:
            app.run()
