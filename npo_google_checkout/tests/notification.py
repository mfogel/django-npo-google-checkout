"""
Tests for the notifcation API.
"""

from xml.etree import ElementTree
from os.path import dirname, join

from django.test import TestCase
from django.core.urlresolvers import reverse

from .google_checkout_client import GCClient

RESPONSE_FRMT_STR = """<notification-acknowledgment xmlns="http://checkout.google.com/schema/2" serial-number="{serial_number}" />"""


class NotificationTests(TestCase):
    client_class = GCClient

    # TODO: a good way to test csrf stuff? client should
    #       not send any csrf tokens

    def setUp(self):
        self.path = reverse('ngc-notification-listener')
        self.data_dir = join(dirname(__file__), 'data')

    def test_basic(self):
        """
        The data files, in the same order as GC sandbox sends them out:
            'new-order-notification'
            'order-state-change-notification_1-reviewing-chargeable'
            'risk-information-notification'
            'authorization-amount-notification'
            'order-state-change-notification_2-chargeable-charging'
            'order-state-change-notification_3-charging-charged'
            'charge-amount-notification'
        """

        xml = open(join(self.data_dir, 'new-order-notification.xml')).read()
        serial_number = ElementTree.XML(xml).get('serial-number')
        res = self.client.post_notification(self.path, xml)
        self.assertEqual(res.raw_post_data,
                RESPONSE_FRMT_STR.format(serial_number=serial_number))
        # TODO: test some internal state
