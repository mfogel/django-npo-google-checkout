"""
Tests for the notifcation API.
"""

from xml.etree import ElementTree
from os.path import dirname, join

from django.core.urlresolvers import reverse
from django.conf import settings
from django.test import TestCase

from .google_checkout_client import GCClient

RESPONSE_FRMT_STR = """<notification-acknowledgment xmlns="http://checkout.google.com/schema/2" serial-number="{serial_number}" />"""


class NotificationTests(TestCase):
    client_class = GCClient

    # TODO: a good way to test csrf stuff? client should
    #       not send any csrf tokens

    def setUp(self):
        self.path = reverse('ngc-notification-listener')
        self.data_dir = join(dirname(__file__), 'data')
        settings.NGC_BACKEND = \
                'npo_google_checkout.backends.default.DefaultBackend'

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

        # TODO: test internal state in between these calls
        res = self._base_notification('new-order-notification.xml')
        res = self._base_notification('order-state-change-notification_1-reviewing-chargeable.xml')
        res = self._base_notification('risk-information-notification.xml')
        res = self._base_notification('authorization-amount-notification.xml')
        res = self._base_notification('order-state-change-notification_2-chargeable-charging.xml')
        res = self._base_notification('order-state-change-notification_3-charging-charged.xml')
        res = self._base_notification('charge-amount-notification.xml')


    def _base_notification(self, filename):
        xml = open(join(self.data_dir, filename)).read()
        serial_number = ElementTree.XML(xml).get('serial-number')
        response = self.client.post_notification(self.path, xml)
        self.assertEqual(response.content.strip(),
                RESPONSE_FRMT_STR.format(serial_number=serial_number))
        return response
