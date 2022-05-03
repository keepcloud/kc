from kc.utils import test
from kc.cli.main import KCTestApp


class CliTestCaseStackStatus(test.KCTestCase):

    def test_kc_cli_stack_services_status_nginx(self):
        with KCTestApp(argv=['stack', 'status', '--nginx']) as app:
            app.run()

    def test_kc_cli_stack_services_status_php_fpm(self):
        with KCTestApp(argv=['stack', 'status', '--php']) as app:
            app.run()

    def test_kc_cli_stack_services_status_mysql(self):
        with KCTestApp(argv=['stack', 'status', '--mysql']) as app:
            app.run()

    def test_kc_cli_stack_services_status_all(self):
        with KCTestApp(argv=['stack', 'status']) as app:
            app.run()
