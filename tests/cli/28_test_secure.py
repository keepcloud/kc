from kc.utils import test
from kc.cli.main import KCTestApp


class CliTestCaseSecure(test.KCTestCase):

    def test_kc_cli_secure_auth(self):
        with KCTestApp(argv=['secure', '--auth', 'abc', 'superpass']) as app:
            app.run()

    def test_kc_cli_secure_port(self):
        with KCTestApp(argv=['secure', '--port', '22222']) as app:
            app.run()

    def test_kc_cli_secure_ip(self):
        with KCTestApp(argv=['secure', '--ip', '172.16.0.1']) as app:
            app.run()
