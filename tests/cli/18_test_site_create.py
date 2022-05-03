from kc.utils import test
from kc.cli.main import KCTestApp


class CliTestCaseSiteCreate(test.KCTestCase):

    def test_kc_cli_site_create_html(self):
        with KCTestApp(argv=['site', 'create', 'html.com',
                             '--html']) as app:
            app.config.set('kc', '', True)
            app.run()

    def test_kc_cli_site_create_php(self):
        with KCTestApp(argv=['site', 'create', 'php.com',
                             '--php']) as app:
            app.run()

    def test_kc_cli_site_create_mysql(self):
        with KCTestApp(argv=['site', 'create', 'mysql.com',
                             '--mysql']) as app:
            app.run()

    def test_kc_cli_site_create_wp(self):
        with KCTestApp(argv=['site', 'create', 'wp.com',
                             '--wp']) as app:
            app.run()

    def test_kc_cli_site_create_wpsubdir(self):
        with KCTestApp(argv=['site', 'create', 'wpsubdir.com',
                             '--wpsubdir']) as app:
            app.run()

    def test_kc_cli_site_create_wpsubdomain(self):
        with KCTestApp(argv=['site', 'create', 'wpsubdomain.com',
                             '--wpsubdomain']) as app:
            app.run()

    def test_kc_cli_site_create_wpfc(self):
        with KCTestApp(argv=['site', 'create', 'wpfc.com',
                             '--wpfc']) as app:
            app.run()

    def test_kc_cli_site_create_wpsc(self):
        with KCTestApp(argv=['site', 'create', 'wpsc.com',
                             '--wpsc']) as app:
            app.run()

    def test_kc_cli_site_create_wpce(self):
        with KCTestApp(argv=['site', 'create', 'wpce.com',
                             '--wpce']) as app:
            app.run()

    def test_kc_cli_site_create_wprocket(self):
        with KCTestApp(argv=['site', 'create', 'wprocket.com',
                             '--wprocket']) as app:
            app.run()
