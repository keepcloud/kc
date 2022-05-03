from kc.utils import test
from kc.cli.main import KCTestApp


class CliTestCaseStackStart(test.KCTestCase):

    def test_kc_cli_stack_services_start_nginx(self):
        with KCTestApp(argv=['stack', 'start', '--nginx']) as app:
            app.run()

    def test_kc_cli_stack_services_start_php_fpm(self):
        with KCTestApp(argv=['stack', 'start', '--php']) as app:
            app.run()

    def test_kc_cli_stack_services_start_mysql(self):
        with KCTestApp(argv=['stack', 'start', '--mysql']) as app:
            app.run()

    def test_kc_cli_stack_services_start_all(self):
        with KCTestApp(argv=['stack', 'start']) as app:
            app.run()
