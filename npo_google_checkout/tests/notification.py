"""
Tests for the notification API.
"""

from datetime import datetime, timedelta
from dateutil.parser import parse as dt_parse
from decimal import Decimal
from os.path import dirname, join
import time
from xml.etree.ElementTree import XML

from django.conf import settings
from django.core.urlresolvers import reverse
from django.test import TestCase

from .google_checkout_client import GCClient
from ..models import GoogleOrder
from ..xpath import *

RESPONSE_FRMT_STR = """<notification-acknowledgment xmlns="http://checkout.google.com/schema/2" serial-number="{serial_number}" />"""


# FIXME: a good way to test csrf stuff? client should
#        not send any csrf tokens

# FIXME: a good way to test signals being sent out?

# FIXME: test setting of associated cart via <merchant-private-data>?
#        this would require a short custom testing backend with a fake cart


class NotificationTestsMixin(object):
    client_class = GCClient
    data_dir = join(dirname(__file__), 'data', 'notification')

    def setUp(self):
        self.url = reverse('ngc-notification-listener')
        settings.NGC_BACKEND = \
            'npo_google_checkout.backends.default.DefaultBackend'

    def _base_notification(self, test_xml_fn):
        xml = open(join(self.data_dir, test_xml_fn)).read()
        serial_number = XML(xml).get('serial-number')
        response = self.client.post_notification(self.url, xml)
        self.assertEqual(response.content.strip(),
                RESPONSE_FRMT_STR.format(serial_number=serial_number))
        return response

    def _open_xml(self, fn):
        path = join(self.data_dir, fn)
        xml = XML(open(path).read())
        return xml

    def _extract_timestamp(self, notify_xml):
        """Extract the timestamp, converted to the local timezone"""
        ts_utc = dt_parse(notify_xml.findtext(xpq_timestamp))
        return self._trans_utc_to_local(ts_utc)

    def _trans_utc_to_local(self, ts_utc):
        ts_local = ts_utc - timedelta(seconds=time.timezone)
        ts_local = ts_local.replace(tzinfo=None)
        return ts_local


class NotificationNewOrderMinimalTests(NotificationTestsMixin, TestCase):
    new_order_minimal_fn = 'new-order_minimal.xml'

    def setUp(self):
        super(NotificationNewOrderMinimalTests, self).setUp()

        # extract exprected answers from the test data
        xml = self._open_xml(self.new_order_minimal_fn)
        self.order_number = long(xml.findtext(xpq_order_number))
        self.timestamp = self._extract_timestamp(xml)

    def test_minimal(self):
        self._base_notification(self.new_order_minimal_fn)
        go = GoogleOrder.objects.get()
        # key 'minimal' assertiong
        self.assertIsNone(go.cart_id)
        self.assertIsNone(go.dt_expires)
        # basic assertions
        self.assertEqual(go.number, self.order_number)
        self.assertEqual(go.dt_init, self.timestamp)
        self.assertEqual(go.state, GoogleOrder.REVIEWING_STATE)
        self.assertEqual(go.amount_charged, 0)
        self.assertEqual(
            go.last_notify_type, GoogleOrder.NEW_ORDER_NOTIFY_TYPE)
        self.assertEqual(go.last_notify_dt, self.timestamp)


class NotificationBasicTests(NotificationTestsMixin, TestCase):

    # The data files, in the same order as GC sandbox sends them out:
    new_order_fn = 'new-order.xml'
    order_state_change_1_fn = 'order-state-change_1-reviewing-chargeable.xml'
    risk_information_fn = 'risk-information.xml'
    authorization_amount_fn = 'authorization-amount.xml'
    order_state_change_2_fn = 'order-state-change_2-chargeable-charging.xml'
    order_state_change_3_fn = 'order-state-change_3-charging-charged.xml'
    charge_amount_fn = 'charge-amount.xml'

    def setUp(self):
        super(NotificationBasicTests, self).setUp()

        # extract exprected answers from the test data
        no_xml = self._open_xml(self.new_order_fn)
        self.order_number = long(no_xml.findtext(xpq_order_number))
        self.new_order_timestamp = self._extract_timestamp(no_xml)
        expires_utc = dt_parse(no_xml.findtext(xpq_good_until_date))
        self.dt_expires = self._trans_utc_to_local(expires_utc)

        osc1_xml = self._open_xml(self.order_state_change_1_fn)
        self.order_state_change_1_timestamp = self._extract_timestamp(osc1_xml)

        osc2_xml = self._open_xml(self.order_state_change_2_fn)
        self.order_state_change_2_timestamp = self._extract_timestamp(osc2_xml)

        osc3_xml = self._open_xml(self.order_state_change_3_fn)
        self.order_state_change_3_timestamp = self._extract_timestamp(osc3_xml)

        ri_xml = self._open_xml(self.risk_information_fn)
        self.risk_information_timestamp = self._extract_timestamp(ri_xml)

        aa_xml = self._open_xml(self.authorization_amount_fn)
        self.authorization_amount_timestamp = self._extract_timestamp(aa_xml)

        ca_xml = self._open_xml(self.charge_amount_fn)
        self.charge_amount_timestamp = self._extract_timestamp(ca_xml)
        self.total_charge_amount = \
            Decimal(ca_xml.findtext(xpq_total_charge_amount))


    def test_basic(self):
        """
        Go through the basic no-frills set of notifications GC sends when
        everything goes easy and simple. No funny stuff.
        """

        self._base_notification(self.new_order_fn)
        go = self._base_assertions(
                GoogleOrder.REVIEWING_STATE,
                GoogleOrder.NEW_ORDER_NOTIFY_TYPE,
                self.new_order_timestamp)
        self.assertEqual(go.dt_init, self.new_order_timestamp)
        self.assertEqual(go.amount_charged, 0)
        self.assertEqual(go.dt_expires, self.dt_expires)

        self._base_notification(self.order_state_change_1_fn)
        go = self._base_assertions(
                GoogleOrder.CHARGEABLE_STATE,
                GoogleOrder.ORDER_STATE_CHANGE_NOTIFY_TYPE,
                self.order_state_change_1_timestamp)

        self._base_notification(self.risk_information_fn)
        go = self._base_assertions(
                GoogleOrder.CHARGEABLE_STATE,
                GoogleOrder.RISK_INFORMATION_NOTIFY_TYPE,
                self.risk_information_timestamp)

        self._base_notification(self.authorization_amount_fn)
        go = self._base_assertions(
                GoogleOrder.CHARGEABLE_STATE,
                GoogleOrder.AUTHORIZATION_AMOUNT_NOTIFY_TYPE,
                self.authorization_amount_timestamp)

        self._base_notification(self.order_state_change_2_fn)
        go = self._base_assertions(
                GoogleOrder.CHARGING_STATE,
                GoogleOrder.ORDER_STATE_CHANGE_NOTIFY_TYPE,
                self.order_state_change_2_timestamp)

        self._base_notification(self.order_state_change_3_fn)
        go = self._base_assertions(
                GoogleOrder.CHARGED_STATE,
                GoogleOrder.ORDER_STATE_CHANGE_NOTIFY_TYPE,
                self.order_state_change_3_timestamp)

        self._base_notification(self.charge_amount_fn)
        go = self._base_assertions(
                GoogleOrder.CHARGED_STATE,
                GoogleOrder.CHARGE_AMOUNT_NOTIFY_TYPE,
                self.charge_amount_timestamp)
        self.assertEqual(go.amount_charged, self.total_charge_amount)

    def _base_assertions(self, state, notify_type, timestamp):
        go = GoogleOrder.objects.get()
        self.assertEqual(go.number, self.order_number)
        self.assertEqual(go.state, state)
        self.assertEqual(go.last_notify_type, notify_type)
        self.assertEqual(go.last_notify_dt, timestamp)
        return go
