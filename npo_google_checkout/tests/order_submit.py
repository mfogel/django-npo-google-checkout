"""
Tests for submitting an order to GC
"""

from datetime import datetime
from os.path import dirname, join
from xml.etree.ElementTree import XML

from django.core.urlresolvers import reverse
from django.dispatch import receiver
from django.test import TestCase

from .. import settings as ngc_settings
from ..models import OrderSubmitRedirect
from ..signals import order_submit
from ..views import OrderSubmitView
from ..xpath import xpq_redirect_url


class OrderSubmitTests(TestCase):
    fixtures = ['ngc_auth_user']
    data_dir = join(dirname(__file__), 'data', 'order_submit')
    checkout_redirect_fn = 'checkout-redirect.xml'

    def order_submit_receiver(self, sender, **kwargs):
        "Receiver to test signals sent out"
        self.signal_kwargs = kwargs

    def setUp(self):
        self.path = reverse('ngc-order-submit')
        order_submit.connect(self.order_submit_receiver)

        # semi-hacky. get the order-submit requiest to hit the file on disk
        # see use of 'order_submit_url' in views.py
        ngc_settings.API_BASE_URL = 'file://{0}'.format(self.data_dir)
        ngc_settings.MERCHANT_ID = self.checkout_redirect_fn

        checkout_redirect_xml_path = \
            OrderSubmitView.order_submit_frmt_str.format(
                NGC_API_BASE_URL=self.data_dir,
                NGC_MERCHANT_ID=self.checkout_redirect_fn)

        cr_xml = XML(open(join(checkout_redirect_xml_path)).read())
        self.serial_number = cr_xml.get('serial-number')
        self.redirect_url = cr_xml.find(xpq_redirect_url).text

    def test_basic(self):
        # user makes request to order redirect page
        self.client.login(username='test', password='test')
        response = self.client.post(self.path)

        # django 1.3: TestCase.assertRedirects can't be used for ext. urls
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], self.redirect_url)

        # check the db populated correctly
        osr = OrderSubmitRedirect.objects.get()
        self.assertEqual(osr.redirect_url, self.redirect_url)
        self.assertLess(osr.dt, datetime.now())

        # check the signals was sent correctly
        self.assertEqual(self.signal_kwargs['redirect_url'], self.redirect_url)
        # UPGRADE: when making tests with a testing backend, could test
        #   'cart' better
        self.assertEqual( self.signal_kwargs['cart'], None)
