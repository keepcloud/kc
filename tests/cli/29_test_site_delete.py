from kc.utils import test
from kc.cli.main import KCTestApp


class CliTestCaseSiteDelete(test.KCTestCase):

    def test_kc_cli_site_detele(self):
        with KCTestApp(argv=['site', 'delete', 'html.com',
                             '--force']) as app:
            app.run()

    def test_kc_cli_site_detele_all(self):
        with KCTestApp(argv=['site', 'delete', 'wp.com',
                             '--all', '--force']) as app:
            app.run()

    def test_kc_cli_site_detele_db(self):
        with KCTestApp(argv=['site', 'delete', 'mysql.com',
                             '--db', '--force']) as app:
            app.run()

    def test_kc_cli_site_detele_files(self):
        with KCTestApp(argv=['site', 'delete', 'php.com',
                             '--files', '--force']) as app:
            app.run()
