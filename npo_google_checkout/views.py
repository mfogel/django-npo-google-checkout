import base64
import logging
import urllib, urllib2
from xml.etree import ElementTree

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.http import Http404, HttpResponseServerError
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext_lazy as _
from django.views.generic import RedirectView, TemplateView
from django.views.decorators.csrf import csrf_exempt

from signup_login.decorators import login_required

from .backends import get_backend
from .signals import order_submit
from . import NGC_ORDER_SUBMIT_URL

backend = get_backend(settings.NGC_BACKEND)
logger = logging.getLogger('django.request')


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
        xml = self.order_submit_backend.get_order_submit_xml()

        request = urllib2.Request(NGC_ORDER_SUBMIT_URL, headers=headers)
        request.add_data(xml)

        handle = urllib2.urlopen(request, timeout=settings.NGC_HTTP_TIMEOUT)
        try:
            # http://code.google.com/apis/checkout/developer/Google_Checkout_XML_API_Guide_for_Nonprofit_Organizations.html#create_checkout_cart
            tree = ElementTree.XML(handle.read())
            redirect_url = tree[0].text;
        except:
            return HttpResponseServerError("Sorry - we're having trouble communicating with google checkout.")
        return redirect_url

    @method_decorator(login_required)
    def post(self, request, *args, **kwargs):
        self.order_submit_backend = backend.get_order_submit_instance(request)
        if not self.order_submit_backend.has_cart():
            raise Http404("User has no cart")
        resp = super(OrderSubmitView, self).get(request, *args, **kwargs)
        order_submit.send(
                sender=self,
                cart=self.order_submit_backend.get_cart(),
                redirect_url=self.get_redirect_url())
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
        logger.info("GC notification received.", extra={'request': request})
        # TODO:
        #   - determine serial number, google order number, set on self
        #   - determine notifcation type
        #   - dispatch django signal as appropriate
        #   - call backend function
        #       - if error, return a 500. Else, return a 200 via...
        return super(NotificationListenerView, self).get(
                request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(NotificationListenerView, self).get_context_data(
                **kwargs)
        # TODO: actually parse the serial number out.
        context.update({
            #'serial_number': self.serial_number,
            'serial_number': '12349493932-23948',
        })
        return context
