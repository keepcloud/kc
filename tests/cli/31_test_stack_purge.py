from kc.utils import test
from kc.cli.main import KCTestApp


class CliTestCaseStackPurge(test.KCTestCase):

    def test_kc_cli_stack_purge_web(self):
        with KCTestApp(
                argv=['stack', 'purge', '--web', '--force']) as app:
            app.run()

    def test_kc_cli_stack_purge_admin(self):
        with KCTestApp(
                argv=['stack', 'purge', '--admin', '--force']) as app:
            app.run()

    def test_kc_cli_stack_purge_nginx(self):
        with KCTestApp(
                argv=['stack', 'purge', '--nginx', '--force']) as app:
            app.run()

    def test_kc_cli_stack_purge_php(self):
        with KCTestApp(argv=['stack', 'purge',
                                      '--php', '--force']) as app:
            app.run()

    def test_kc_cli_stack_purge_mysql(self):
        with KCTestApp(argv=['stack', 'purge',
                                      '--mysql', '--force']) as app:
            app.run()

    def test_kc_cli_stack_purge_wpcli(self):
        with KCTestApp(argv=['stack', 'purge',
                                      '--wpcli', '--force']) as app:
            app.run()

    def test_kc_cli_stack_purge_phpmyadmin(self):
        with KCTestApp(
                argv=['stack', 'purge', '--phpmyadmin', '--force']) as app:
            app.run()

    def test_kc_cli_stack_purge_adminer(self):
        with KCTestApp(
                argv=['stack', 'purge', '--adminer', '--force']) as app:
            app.run()

    def test_kc_cli_stack_purge_utils(self):
        with KCTestApp(argv=['stack', 'purge',
                                      '--utils', '--force']) as app:
            app.run()
