from unittest import TestCase
from machines.templatetags.training_extras import price_format

class PriceTests(TestCase):
    def test_price_format(self):
        self.assertEqual(price_format(12), "12 CHF")
        self.assertEqual(price_format(12.3), "12.30 CHF")
        self.assertEqual(price_format(12.34), "12.34 CHF")
        self.assertEqual(price_format(12.345), "12.35 CHF")
        self.assertEqual(price_format(4.321), "4.32 CHF")