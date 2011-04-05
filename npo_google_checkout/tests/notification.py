"""
Tests for the notifcation API.
"""

from datetime import datetime, timedelta
from dateutil.parser import parse as dt_parse
from decimal import Decimal
from os.path import dirname, join
import time
from xml.etree.ElementTree import XML

from django.core.urlresolvers import reverse
from django.conf import settings
from django.test import TestCase

from .google_checkout_client import GCClient
from ..models import GoogleOrder

RESPONSE_FRMT_STR = """<notification-acknowledgment xmlns="http://checkout.google.com/schema/2" serial-number="{serial_number}" />"""


class NotificationTests(TestCase):
    client_class = GCClient

    # The data files, in the same order as GC sandbox sends them out:
    data_dir = join(dirname(__file__), 'data')
    new_order_path = join(data_dir, 'new-order-notification.xml')
    order_state_change_1_path = \
        join(data_dir, 'order-state-change-notification_1-reviewing-chargeable.xml')
    risk_information_path = join(data_dir, 'risk-information-notification.xml')
    authorization_amount_path = \
        join(data_dir, 'authorization-amount-notification.xml')
    order_state_change_2_path = \
        join(data_dir, 'order-state-change-notification_2-chargeable-charging.xml')
    order_state_change_3_path = \
        join(data_dir, 'order-state-change-notification_3-charging-charged.xml')
    charge_amount_path = join(data_dir, 'charge-amount-notification.xml')

    # extracting data from those files
    xmlns = 'http://checkout.google.com/schema/2'
    xpq_order_number = '{{{0}}}google-order-number'.format(xmlns)
    xpq_timestamp = '{{{0}}}timestamp'.format(xmlns)
    xpq_total_charge_amount= '{{{0}}}total-charge-amount'.format(xmlns)


    # FIXME: a good way to test csrf stuff? client should
    #        not send any csrf tokens

    # FIXME: a good way to test signals being sent out?

    def setUp(self):
        self.path = reverse('ngc-notification-listener')
        settings.NGC_BACKEND = \
            'npo_google_checkout.backends.default.DefaultBackend'

        # extract some data from the test data
        no_xml = XML(open(join(self.new_order_path)).read())
        self.order_number = long(no_xml.find(self.xpq_order_number).text)
        self.new_order_timestamp = self._extract_timestamp(no_xml)

        osc1_xml = XML(open(join(self.order_state_change_1_path)).read())
        self.order_state_change_1_timestamp = self._extract_timestamp(osc1_xml)

        osc2_xml = XML(open(join(self.order_state_change_2_path)).read())
        self.order_state_change_2_timestamp = self._extract_timestamp(osc2_xml)

        osc3_xml = XML(open(join(self.order_state_change_3_path)).read())
        self.order_state_change_3_timestamp = self._extract_timestamp(osc3_xml)

        ri_xml = XML(open(join(self.risk_information_path)).read())
        self.risk_information_timestamp = self._extract_timestamp(ri_xml)

        aa_xml = XML(open(join(self.authorization_amount_path)).read())
        self.authorization_amount_timestamp = self._extract_timestamp(aa_xml)

        ca_xml = XML(open(join(self.charge_amount_path)).read())
        self.charge_amount_timestamp = self._extract_timestamp(ca_xml)
        self.total_charge_amount = Decimal(ca_xml.find(self.xpq_total_charge_amount).text)

    def _extract_timestamp(self, notify_xml):
        """Extract the timestamp, converted to the local timezone"""
        ts_utc = dt_parse(notify_xml.find(self.xpq_timestamp).text)
        ts_local = ts_utc - timedelta(seconds=time.timezone)
        ts_local = ts_local.replace(tzinfo=None)
        return ts_local

    def test_basic(self):
        """
        Go through the basic no-frills set of notifications GC sends when
        everything goes easy and simple. No funny stuff.
        """

        res, go = self._base_notification(self.new_order_path,
                GoogleOrder.REVIEWING_STATE, GoogleOrder.NEW_ORDER_NOTIFY_TYPE,
                self.new_order_timestamp)
        self.assertEqual(go.dt_init, self.new_order_timestamp)
        self.assertEqual(go.amount_charged, 0)

        res, go = self._base_notification(self.order_state_change_1_path,
                GoogleOrder.CHARGEABLE_STATE,
                GoogleOrder.ORDER_STATE_CHANGE_NOTIFY_TYPE,
                self.order_state_change_1_timestamp)

        res, go = self._base_notification(self.risk_information_path,
                GoogleOrder.CHARGEABLE_STATE,
                GoogleOrder.RISK_INFORMATION_NOTIFY_TYPE,
                self.risk_information_timestamp)

        res, go = self._base_notification(self.authorization_amount_path,
                GoogleOrder.CHARGEABLE_STATE,
                GoogleOrder.AUTHORIZATION_AMOUNT_NOTIFY_TYPE,
                self.authorization_amount_timestamp)

        res, go = self._base_notification(self.order_state_change_2_path,
                GoogleOrder.CHARGING_STATE,
                GoogleOrder.ORDER_STATE_CHANGE_NOTIFY_TYPE,
                self.order_state_change_2_timestamp)

        res, go = self._base_notification(self.order_state_change_3_path,
                GoogleOrder.CHARGED_STATE,
                GoogleOrder.ORDER_STATE_CHANGE_NOTIFY_TYPE,
                self.order_state_change_3_timestamp)

        res, go = self._base_notification(self.charge_amount_path,
                GoogleOrder.CHARGED_STATE,
                GoogleOrder.CHARGE_AMOUNT_NOTIFY_TYPE,
                self.charge_amount_timestamp)
        self.assertEqual(go.amount_charged, self.total_charge_amount)

    def _base_notification(self,
            test_xml_path, new_state, new_notify_type, timestamp):
        xml = open(join(test_xml_path)).read()
        serial_number = XML(xml).get('serial-number')
        response = self.client.post_notification(self.path, xml)
        self.assertEqual(response.content.strip(),
                RESPONSE_FRMT_STR.format(serial_number=serial_number))

        go = GoogleOrder.objects.get()
        self.assertEqual(go.number, self.order_number)
        self.assertEqual(go.state, new_state)
        self.assertEqual(go.last_notify_type, new_notify_type)
        self.assertEqual(go.last_notify_dt, timestamp)

        return response, go
