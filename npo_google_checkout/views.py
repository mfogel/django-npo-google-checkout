import base64
from datetime import timedelta
from dateutil.parser import parse as dt_parse
from decimal import Decimal
import logging
import time
import urllib, urllib2
from xml.etree.ElementTree import XML

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.http import Http404, HttpResponseServerError
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext_lazy as _
from django.views.generic import RedirectView, TemplateView
from django.views.decorators.csrf import csrf_exempt

from signup_login.decorators import login_required

from .backends import get_backend_class
from .models import *
from .signals import *
from .xpath import *

logger = logging.getLogger('django.request')
xmlns = 'http://checkout.google.com/schema/2'


class OrderSubmitView(RedirectView):
    permanent = False

    def get(self, *args, **kwargs):
        raise Http404("GET method not allowed.")

    def get_redirect_url(self, **kwagrs):
        # example:
        # http://code.google.com/p/chippysshop/source/browse/googlecheckout.py
        auth_string = 'Basic {0}'.format(base64.b64encode(
            settings.NGC_MERCHANT_ID + ':' + settings.NGC_MERCHANT_KEY))
        headers = {
                'Content-Type': 'application/xml; charset=UTF-8',
                'Accept': 'application/xml; charset=UTF-8',
                'Authorization': auth_string,
            }
        xml = self.backend.get_order_submit_xml()

        req = urllib2.Request(settings.NGC_ORDER_SUBMIT_URL, headers=headers)
        req.add_data(xml)

        handle = urllib2.urlopen(req, timeout=settings.NGC_HTTP_TIMEOUT)
        self.gc_raw_post_data = handle.read()
        try:
            # http://code.google.com/apis/checkout/developer/Google_Checkout_XML_API_Guide_for_Nonprofit_Organizations.html#create_checkout_cart
            redirect_xml = XML(self.gc_raw_post_data)
            redirect_url = redirect_xml.find(xpq_redirect_url).text;
            self.serial_number = redirect_xml.get('serial-number')
        except:
            return HttpResponseServerError("Sorry - we're having trouble communicating with google checkout.")
        return redirect_url

    @method_decorator(login_required)
    def post(self, request, *args, **kwargs):
        backend_class = get_backend_class(settings.NGC_BACKEND)
        self.backend = backend_class(request)
        cart = self.backend.get_cart()
        redirect_url = self.get_redirect_url()
        resp = super(OrderSubmitView, self).get(request, *args, **kwargs)

        logger.info(
            "GC order-redirect #{0} received.".format(self.serial_number),
            extra={'request': request, 'raw_post_data': self.gc_raw_post_data})

        OrderSubmitRedirect.objects.create(
                cart=cart, redirect_url=redirect_url)
        order_submit.send(self, cart=cart, redirect_url=redirect_url)
        return resp


class NotificationListenerView(TemplateView):
    template_name = 'npo_google_checkout/notification_acknowledgment.html'

    def get(self, *args, **kwargs):
        raise Http404("GET method not allowed.")

    # TODO: this fails when on the post. intended?
    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
      return super(NotificationListenerView, self).dispatch(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        notify_xml = XML(request.raw_post_data)
        self.notify_type = self._extract_notify_type(notify_xml)
        self.notify_type_const = \
            GoogleOrder.trans_notify_type_const(self.notify_type)
        self.timestamp = self._extract_timestamp(notify_xml)
        self.serial_number = notify_xml.get('serial-number')
        self.order_number = long(notify_xml.findtext(xpq_order_number))

        private_data = notify_xml.findtext(xpq_merchant_private_data)
        backend_class = get_backend_class(settings.NGC_BACKEND)
        self.backend = backend_class(request, private_data=private_data)
        self.cart = self.backend.get_cart()

        logger.info(
            "GC {0} #{1} received.".format(
                self.notify_type, self.serial_number),
            extra={'request': request})

        # notification type-specific handling
        if self.notify_type_const == GoogleOrder.NEW_ORDER_NOTIFY_TYPE:
            self._post_new_order()
        else:
            order = GoogleOrder.objects.get(number=self.order_number)
            order.last_notify_type = self.notify_type_const
            order.last_notify_dt = self.timestamp
            if self.notify_type_const == GoogleOrder.ORDER_STATE_CHANGE_NOTIFY_TYPE:
                self._post_order_state_change(order, notify_xml)
            elif self.notify_type_const == GoogleOrder.RISK_INFORMATION_NOTIFY_TYPE:
                self._post_risk_informaiton(order, notify_xml)
            elif self.notify_type_const == GoogleOrder.AUTHORIZATION_AMOUNT_NOTIFY_TYPE:
                self._post_authorization_amount(order, notify_xml)
            elif self.notify_type_const == GoogleOrder.CHARGE_AMOUNT_NOTIFY_TYPE:
                self._post_charge_amount(order, notify_xml)
            else:
                msg = "Unrecognized notification '{0}' recieved". \
                        format(self.notify_type)
                raise RuntimeError(msg)

        return super(NotificationListenerView, self).get(
                request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(NotificationListenerView, self). \
            get_context_data(**kwargs)
        context.update({
            'serial_number': self.serial_number,
        })
        return context

    def _extract_notify_type(self, notify_xml):
        notify_type = notify_xml.tag
        if notify_type[0] == '{':
            r_indx = notify_type.find('}')
            notify_type = notify_type[r_indx+1:]
        return notify_type

    def _extract_timestamp(self, notify_xml):
        """Extract the timestamp, converted to the local timezone"""
        ts_utc = dt_parse(notify_xml.find(xpq_timestamp).text)
        ts_local = ts_utc - timedelta(seconds=time.timezone)
        ts_local = ts_local.replace(tzinfo=None)
        return ts_local

    def _post_new_order(self):
        order = GoogleOrder.objects.create(
                cart=self.cart, number=self.order_number,
                dt_init=self.timestamp, last_notify_dt=self.timestamp)
        notification_new_order.send(self, cart=self.cart, order=order)

    def _post_order_state_change(self, order, notify_xml):
        old_state = order.state
        new_state_string = notify_xml.findtext(xpq_new_state)
        new_state = GoogleOrder.trans_state_const(new_state_string)
        order.state = new_state
        order.save()
        notification_order_state_change.send(self,
                cart=self.cart, order=order,
                old_state=old_state, new_state=new_state)

    def _post_risk_informaiton(self, order, notify_xml):
        order.save()
        risk_info_xml_node = notify_xml.find(xpq_risk_info)
        notification_risk_information.send(self,
                cart=self.cart, order=order,
                risk_info_xml_node=risk_info_xml_node)

    def _post_authorization_amount(self, order, notify_xml):
        order.save()
        auth_amount = Decimal(notify_xml.findtext(xpq_authorization_amount))
        notification_risk_information.send(self,
                cart=self.cart, order=order,
                authorization_amount=auth_amount)

    def _post_charge_amount(self, order, notify_xml):
        order.amount_charged = \
            Decimal(notify_xml.find(xpq_total_charge_amount).text)
        order.save()
        latest_amount = Decimal(notify_xml.findtext(xpq_latest_charge_amount))
        notification_risk_information.send(self,
                cart=self.cart, order=order,
                latest_amount=latest_amount, total_amount=order.amount_charged)
