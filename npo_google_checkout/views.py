import base64
import logging
import time
import urllib, urllib2
from datetime import timedelta
from dateutil.parser import parse as dt_parse
from decimal import Decimal
from xml.etree.ElementTree import XML

from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpResponseServerError
from django.utils.decorators import method_decorator
from django.views.generic import RedirectView, TemplateView
from django.views.decorators.csrf import csrf_exempt

from . import settings as ngc_settings
from .backends import get_backend_class
from .models import *
from .signals import *
from .xpath import *

logger = logging.getLogger('django.request')


class OrderSubmitView(RedirectView):
    permanent = False
    order_submit_frmt_str = \
        '{NGC_API_BASE_URL}/merchantCheckout/Donations/{NGC_MERCHANT_ID}'

    def syncronous_gc_request(self, url, data):
        # example:
        # http://code.google.com/p/chippysshop/source/browse/googlecheckout.py
        auth_string_plain_text = ':'.join((self.backend.get_merchant_id(),
                self.backend.get_merchant_key()))
        auth_string = \
            'Basic {0}'.format(base64.b64encode(auth_string_plain_text))
        headers = {
                'Content-Type': 'application/xml; charset=UTF-8',
                'Accept': 'application/xml; charset=UTF-8',
                'Authorization': auth_string,
            }

        req = urllib2.Request(url, headers=headers)
        req.add_data(data)
        handle = urllib2.urlopen(req, timeout=ngc_settings.HTTP_TIMEOUT)
        response_data = handle.read()
        return response_data

    def get(self, *args, **kwargs):
        raise Http404("GET method not allowed.")

    def get_redirect_xml(self, **kwagrs):
        url = self.order_submit_frmt_str.format(
                NGC_API_BASE_URL=ngc_settings.API_BASE_URL,
                NGC_MERCHANT_ID=self.backend.get_merchant_id())
        xml = self.backend.get_order_submit_xml()

        logger.info(
            "GC order-redirect requested.",
            extra={'request': self.request, 'raw_post_data': xml})

        self.gc_raw_post_data = self.syncronous_gc_request(url, xml)
        try:
            # http://code.google.com/apis/checkout/developer/Google_Checkout_XML_API_Guide_for_Nonprofit_Organizations.html#create_checkout_cart
            redirect_xml = XML(self.gc_raw_post_data)
        except:
            return HttpResponseServerError("Sorry - we're having trouble communicating with google checkout.")
        return redirect_xml

    @method_decorator(login_required)
    def post(self, request, *args, **kwargs):
        backend_class = get_backend_class(ngc_settings.BACKEND)
        self.backend = backend_class(request)
        cart = self.backend.get_cart()

        redirect_xml = self.get_redirect_xml()
        self.url = redirect_xml.findtext(xpq_redirect_url)
        self.serial_number = redirect_xml.get('serial-number')

        resp = super(OrderSubmitView, self).get(request, *args, **kwargs)

        logger.info(
            "GC order-redirect #{0} received.".format(self.serial_number),
            extra={'request': request, 'raw_post_data': self.gc_raw_post_data})

        OrderSubmitRedirect.objects.create(cart=cart, redirect_url=self.url)
        order_submit.send(self, cart=cart, redirect_url=self.url)
        return resp


class NotificationListenerView(TemplateView):
    template_name = 'npo_google_checkout/notification_acknowledgment.html'

    def get(self, *args, **kwargs):
        raise Http404("GET method not allowed.")

    # django bug: this can only be applied to the dispatch() method.
    # http://code.djangoproject.com/ticket/15794
    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
      return super(NotificationListenerView, self).dispatch(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        notify_xml = XML(request.raw_post_data)
        self.notify_type = self._extract_notify_type(notify_xml)
        self.notify_type_const = \
            GoogleOrder.trans_notify_type_const(self.notify_type)

        ts_utc = dt_parse(notify_xml.findtext(xpq_timestamp))
        self.timestamp = self._trans_utc_to_local(ts_utc)

        self.serial_number = notify_xml.get('serial-number')
        self.order_number = long(notify_xml.findtext(xpq_order_number))

        backend_class = get_backend_class(ngc_settings.BACKEND)
        self.backend = backend_class(request, notify_xml=notify_xml)
        self.cart = self.backend.get_cart()

        # if we don't find a cart, we do actually go ahead and continue
        # processing. The idea is the data npo_google_checkout holds should
        # match all of what google checkout holds

        msg_target = "cart '{0}'".format(self.cart) \
                if self.cart else 'unknown cart'
        msg = "GC {0} #{1} received for {2}.".format(
                self.notify_type, self.serial_number, msg_target),
        logger.info(msg, extra={'request': request})

        # notification type-specific handling
        if self.notify_type_const == GoogleOrder.NEW_ORDER_NOTIFY_TYPE:
            self._post_new_order(notify_xml)
        else:
            try:
                order = GoogleOrder.objects.get(number=self.order_number)
            except GoogleOrder.DoesNotExist:
                order = None
            else:
                order.last_notify_type = self.notify_type_const
                order.last_notify_dt = self.timestamp

            if not order:
                # silently ignore notifications for orders we didn't see the
                # new-order-notification for
                pass
            elif self.notify_type_const == GoogleOrder.ORDER_STATE_CHANGE_NOTIFY_TYPE:
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
        # remove xmlns
        if notify_type[0] == '{':
            r_indx = notify_type.find('}')
            notify_type = notify_type[r_indx+1:]
        return notify_type

    def _trans_utc_to_local(self, ts_utc):
        """Translate the given utc datetime object to the local timezone"""
        ts_local = ts_utc - timedelta(seconds=time.timezone)
        ts_local = ts_local.replace(tzinfo=None)
        return ts_local

    def _post_new_order(self, notify_xml):
        expires_utc_node = notify_xml.find(xpq_good_until_date)

        expires = None
        if expires_utc_node is not None:
            expires_utc = dt_parse(expires_utc_node.text)
            expires = self._trans_utc_to_local(expires_utc)

        # check to see if we already have seen that order before inserting it
        # recovering from a db IntegrityError on failure is more complicated
        if not GoogleOrder.objects.filter(number=self.order_number).exists():
            order = GoogleOrder.objects.create(
                    cart=self.cart, number=self.order_number,
                    dt_init=self.timestamp, last_notify_dt=self.timestamp,
                    dt_expires=expires)
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
        notification_authorization_amount.send(self,
                cart=self.cart, order=order,
                authorization_amount=auth_amount)

    def _post_charge_amount(self, order, notify_xml):
        order.amount_charged = \
            Decimal(notify_xml.findtext(xpq_total_charge_amount))
        order.save()
        latest_amount = Decimal(notify_xml.findtext(xpq_latest_charge_amount))
        notification_charge_amount.send(self,
                cart=self.cart, order=order,
                latest_amount=latest_amount, total_amount=order.amount_charged)
