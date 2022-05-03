from kc.utils import test
from kc.cli.main import KCTestApp


class CliTestCaseStackRestart(test.KCTestCase):

    def test_kc_cli_stack_services_restart_nginx(self):
        with KCTestApp(argv=['stack', 'restart', '--nginx']) as app:
            app.run()

    def test_kc_cli_stack_services_restart_php_fpm(self):
        with KCTestApp(argv=['stack', 'restart', '--php']) as app:
            app.run()

    def test_kc_cli_stack_services_restart_mysql(self):
        with KCTestApp(argv=['stack', 'restart', '--mysql']) as app:
            app.run()

    def test_kc_cli_stack_services_restart_all(self):
        with KCTestApp(argv=['stack', 'restart']) as app:
            app.run()
