"""
Tests to ensure your google checkout account is working.

Does a 'hello' command with authentication, see if we get the proper resp.
"""

from xml.etree.ElementTree import XML

from django.test import TestCase

from .. import settings as ngc_settings
from ..backends import get_backend_class
from ..views import OrderSubmitView
from ..xpath import xmlns


class AuthenticationTests(TestCase):

    url_frmt_str = '{NGC_API_BASE_URL}/request/Merchant/{NGC_MERCHANT_ID}'
    request_frmt_str = '<hello xmlns="{xmlns}" />'
    response_frmt_str = '<?xml version="1.0" encoding="UTF-8"?><bye xmlns="{xmlns}" serial-number="{serial_number}" />'

    def test_basic(self):
        """
        http://code.google.com/apis/checkout/developer/Google_Checkout_XML_API_Guide_for_Nonprofit_Organizations.html
        NOTE: example hello commands are broken. should be:
        curl -d '<hello xmlns="http://checkout.google.com/schema/2" />' https://{MERCHANT_ID}:{MERCHANT_KEY}@sandbox.google.com/checkout/api/checkout/v2/request/Merchant/{MERCHANT_ID}
        """
        ngc_settings.BACKEND = \
            'npo_google_checkout.backends.default.DefaultBackend'
        backend = get_backend_class(ngc_settings.BACKEND)(None)
        url = self.url_frmt_str.format(
                NGC_API_BASE_URL=ngc_settings.API_BASE_URL,
                NGC_MERCHANT_ID=backend.get_merchant_id())
        data = self.request_frmt_str.format(xmlns=xmlns)

        osv = OrderSubmitView()
        osv.backend = backend
        response_data = osv.syncronous_gc_request(url, data)
        response_xml_tree = XML(response_data)
        response_serial_number = response_xml_tree.get('serial-number')

        response_stripped = response_data.replace('\r\n', '')
        response_expected = self.response_frmt_str.format(
                xmlns=xmlns, serial_number=response_serial_number)
        self.assertEquals(response_stripped, response_expected)
