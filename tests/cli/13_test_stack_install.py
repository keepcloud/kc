from kc.utils import test
from kc.cli.main import KCTestApp


class CliTestCaseStackInstall(test.KCTestCase):

    def test_kc_cli_stack_install_nginx(self):
        with KCTestApp(argv=['stack', 'install', '--nginx']) as app:
            app.run()

    def test_kc_cli_stack_install_php(self):
        with KCTestApp(argv=['stack', 'install', '--php']) as app:
            app.run()

    def test_kc_cli_stack_install_php73(self):
        with KCTestApp(argv=['stack', 'install', '--php73']) as app:
            app.run()

    def test_kc_cli_stack_install_mysql(self):
        with KCTestApp(argv=['stack', 'install', '--mysql']) as app:
            app.run()

    def test_kc_cli_stack_install_wpcli(self):
        with KCTestApp(argv=['stack', 'install', '--wpcli']) as app:
            app.run()

    def test_kc_cli_stack_install_phpmyadmin(self):
        with KCTestApp(argv=['stack', 'install', '--phpmyadmin']) as app:
            app.run()

    def test_kc_cli_stack_install_adminer(self):
        with KCTestApp(argv=['stack', 'install', '--adminer']) as app:
            app.run()

    def test_kc_cli_stack_install_utils(self):
        with KCTestApp(argv=['stack', 'install', '--utils']) as app:
            app.run()
