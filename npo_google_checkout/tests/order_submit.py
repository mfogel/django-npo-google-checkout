"""
Tests for submitting an order to GC
"""

from datetime import datetime
from os.path import dirname, join
from xml.etree.ElementTree import XML

from django.conf import settings
from django.core.urlresolvers import reverse
from django.test import TestCase

from ..models import OrderSubmitRedirect
from ..xpath import xpq_redirect_url


class OrderSubmitTests(TestCase):
    data_dir = join(dirname(__file__), 'data')
    checkout_redirect_xml_path = join(data_dir, 'checkout-redirect.xml')

    def setUp(self):
        self.path = reverse('ngc-order-submit')
        settings.NGC_ORDER_SUBMIT_URL = \
            'file://{0}'.format(self.checkout_redirect_xml_path)

        cr_xml = XML(open(join(self.checkout_redirect_xml_path)).read())
        self.serial_number = cr_xml.get('serial-number')
        self.redirect_url = cr_xml.find(xpq_redirect_url).text

    def test_basic(self):
        # user makes request to order redirect page
        self.client.login(username='mike', password='test')
        response = self.client.post(self.path)

        # django 1.3: TestCase.assertRedirects can't be used for ext. urls
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], self.redirect_url)

        osr = OrderSubmitRedirect.objects.get()
        self.assertEqual(osr.redirect_url, self.redirect_url)
        self.assertLess(osr.dt, datetime.now())
