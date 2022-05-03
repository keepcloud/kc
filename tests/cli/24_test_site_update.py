from kc.utils import test
from kc.cli.main import KCTestApp


class CliTestCaseSiteUpdate(test.KCTestCase):

    def test_kc_cli_site_update_html(self):
        with KCTestApp(argv=['site', 'update', 'php.com',
                             '--html']) as app:
            app.run()

    def test_kc_cli_site_update_php(self):
        with KCTestApp(argv=['site', 'update', 'html.com',
                             '--php']) as app:
            app.run()

    def test_kc_cli_site_update_mysql(self):
        with KCTestApp(argv=['site', 'update', 'mysql.com',
                             '--html']) as app:
            app.run()

    def test_kc_cli_site_update_wp(self):
        with KCTestApp(argv=['site', 'update', 'mysql.com',
                             '--wp']) as app:
            app.run()

    def test_kc_cli_site_update_wpsubdir(self):
        with KCTestApp(argv=['site', 'update', 'wp.com',
                             '--wpsubdir']) as app:
            app.run()

    def test_kc_cli_site_update_wpsubdomain(self):
        with KCTestApp(argv=['site', 'update', 'wpsubdir.com',
                             '--wpsubdomain']) as app:
            app.run()

    def test_kc_cli_site_update_wpfc(self):
        with KCTestApp(argv=['site', 'update', 'wpsc.com',
                             '--wpfc']) as app:
            app.run()

    def test_kc_cli_site_update_wpsc(self):
        with KCTestApp(argv=['site', 'update', 'wpfc.com',
                             '--wpsc']) as app:
            app.run()
