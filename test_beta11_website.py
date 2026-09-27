"""Regression checks for the staged Beta 11 free-account website.

Run after applying P7: py -3 -m unittest test_beta11_website -v
"""
from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
import unittest
from html.parser import HTMLParser
from pathlib import Path

HTML = (Path(__file__).resolve().parent / 'index.html').read_text(encoding='utf-8')
BILLING_URL = 'https://billing.stripe.com/p/login/eVq7sL0KS5GQazrbLV5c400'


class IdScanner(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = []
        self.handlers = []

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if 'id' in values:
            self.ids.append(values['id'])
        if 'onclick' in values:
            self.handlers.append(values['onclick'])


class Beta11WebsiteTests(unittest.TestCase):
    def test_free_launch_copy_is_visible_and_trial_pricing_is_gone(self):
        pricing = HTML.split('<section class="section pricing-v2 pricing-v3 edge-bubble-zone" id="pricing">', 1)[1].split('<section class="section faq-v3', 1)[0]
        for fragment in ('FREE ACCOUNT', 'go anywhere. for free.', 'Teleport and Route are free',
                         'create a local account', 'id="trial-download"', 'Manage Billing'):
            self.assertIn(fragment, pricing)
        for stale in ('Weekly</div>', 'Monthly</div>', 'Annual</div>', 'Choose Weekly',
                      'Three days with every feature', 'try it free.', 'choose the plan'):
            self.assertNotIn(stale, pricing)

    def test_hero_navigation_and_demo_have_current_account_wording(self):
        self.assertIn('Free Teleport &amp; Route', HTML)
        self.assertIn('<strong>Your account</strong><small>Verified account</small>', HTML)
        self.assertEqual(HTML.count('href="#pricing">Free access</a>'), 3)
        self.assertNotIn('3-day free trial', HTML)
        self.assertIn('name="tapioca-beta11-website"', HTML)

    def test_checkout_ui_and_legacy_purchase_javascript_are_removed(self):
        for fragment in ('id="auth-overlay"', 'openAuthModal(', '/v1/billing/web-checkout',
                         'continueToCheckout(', 'startCheckoutAfterAuth(',
                         'Choose Weekly', 'Choose Monthly', 'Choose Annual'):
            self.assertNotIn(fragment, HTML)
        scanner = IdScanner()
        scanner.feed(HTML)
        self.assertEqual(len(scanner.ids), len(set(scanner.ids)), 'HTML contains duplicate IDs')
        self.assertFalse(any('AuthModal' in x or 'Checkout' in x for x in scanner.handlers))

    def test_legacy_subscribers_can_still_manage_billing(self):
        self.assertGreaterEqual(HTML.count(BILLING_URL), 3)
        self.assertIn('Subscribed to an earlier Tapioca release?', HTML)
        self.assertIn('What if I subscribed before Tapioca became free?', HTML)
        self.assertIn('support@usetapioca.com', HTML)

    def test_no_download_router_or_existing_mobile_demo_was_removed(self):
        for fragment in ('id="hero-windows"', 'id="hero-mac"', 'id="download-windows"',
                         'id="download-mac"', "windows:'/download/windows'", "mac:'/download/mac'",
                         "function detectDesktopOS(){", 'id="demo-map"',
                         'id="download-guide-overlay"'):
            self.assertIn(fragment, HTML)
        self.assertEqual(HTML.count('Sign in with an email code when online'), 2)
        self.assertIn("document.getElementById('download-guide-overlay')?.classList.contains('open')", HTML)

    def test_offline_and_active_computer_faqs_are_accurate(self):
        self.assertIn('Offline road routing requires a saved route or an installed regional routing pack.', HTML)
        self.assertIn('One verified computer is active at a time.', HTML)
        self.assertIn('A Route already in progress on the old computer can continue', HTML)

    def test_full_inline_javascript_parses_in_node(self):
        node = shutil.which('node')
        if node is None:
            self.skipTest('Node.js unavailable; install Node to validate JavaScript syntax')
        self.assertEqual(HTML.count('<script>'), 1)
        self.assertEqual(HTML.count('</script>'), 1)
        src = HTML.split('<script>', 1)[1].split('</script>', 1)[0]
        with tempfile.TemporaryDirectory(prefix='tapioca-beta11-web-') as tmp:
            path = Path(tmp) / 'website.js'
            path.write_text(src, encoding='utf-8')
            result = subprocess.run([node, '--check', str(path)], capture_output=True, text=True, timeout=20)
            self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == '__main__':
    unittest.main()
