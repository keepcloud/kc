from kc.utils import test
from kc.cli.main import KCTestApp


class CliTestCaseStackStop(test.KCTestCase):

    def test_kc_cli_stack_services_stop_nginx(self):
        with KCTestApp(argv=['stack', 'stop', '--nginx']) as app:
            app.run()

    def test_kc_cli_stack_services_stop_php_fpm(self):
        with KCTestApp(argv=['stack', 'stop', '--php']) as app:
            app.run()

    def test_kc_cli_stack_services_stop_mysql(self):
        with KCTestApp(argv=['stack', 'stop', '--mysql']) as app:
            app.run()

    def test_kc_cli_stack_services_stop_all(self):
        with KCTestApp(argv=['stack', 'stop']) as app:
            app.run()
