from kc.utils import test
from kc.cli.main import KCTestApp


class CliTestCaseStackRemove(test.KCTestCase):

    def test_kc_cli_stack_remove_admin(self):
        with KCTestApp(argv=['stack', 'remove', '--admin', '--force']) as app:
            app.run()

    def test_kc_cli_stack_remove_nginx(self):
        with KCTestApp(argv=['stack', 'remove', '--nginx', '--force']) as app:
            app.run()

    def test_kc_cli_stack_remove_php(self):
        with KCTestApp(argv=['stack', 'remove', '--php', '--force']) as app:
            app.run()

    def test_kc_cli_stack_remove_mysql(self):
        with KCTestApp(argv=['stack', 'remove', '--mysql', '--force']) as app:
            app.run()

    def test_kc_cli_stack_remove_wpcli(self):
        with KCTestApp(argv=['stack', 'remove', '--wpcli', '--force']) as app:
            app.run()

    def test_kc_cli_stack_remove_phpmyadmin(self):
        with KCTestApp(argv=['stack', 'remove',
                                      '--phpmyadmin', '--force']) as app:
            app.run()

    def test_kc_cli_stack_remove_adminer(self):
        with KCTestApp(
                argv=['stack', 'remove', '--adminer', '--force']) as app:
            app.run()

    def test_kc_cli_stack_remove_utils(self):
        with KCTestApp(argv=['stack', 'remove', '--utils', '--force']) as app:
            app.run()
