"""Testing utilities for Keepcloud"""
from cement.utils import test
from kc.cli.main import KCTestApp


class KCTestCase(test.CementTestCase):
    app_class = KCTestApp

    def setUp(self):
        """Override setup actions (for every test)."""
        super(KCTestCase, self).setUp()

    def tearDown(self):
        """Override teardown actions (for every test)."""
        super(KCTestCase, self).tearDown()
