import base64
import urllib, urllib2
from xml.etree import ElementTree

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.http import Http404, HttpResponseServerError
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext_lazy as _
from django.views.generic import RedirectView, TemplateView

from signup_login.decorators import login_required

from .backends import get_backend
from . import NGC_ORDER_SUBMIT_URL

backend = get_backend(settings.NGC_BACKEND)


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
        xml = backend.get_order_submit_xml(self.cart_id)

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
        cart_id = backend.get_active_cart_id(request.user)
        if not cart_id:
            raise Http404("User has no cart")
        self.cart_id = cart_id
        # TODO: send out a django signal
        return super(OrderSubmitView, self).get(self, request, *args, **kwargs)


class NotificationListenerView(TemplateView):
    template_name = 'npo_google_checkout/notification_acknowledgment.html'

    def get(self, *args, **kwargs):
        raise Http404("GET method not allowed.")

    def post(self, request, *args, **kwargs):
        # TODO:
        #   - determine serial number, google order number, set on self
        #   - determine notifcation type
        #   - dispatch django signal as appropriate
        #   - call backend function
        #       - if error, return a 500. Else, return a 200 via...
        return super(NotificationListener, self).get(
                self, request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(NotificationListener, self).get_context_data(**kwargs)
        context.update({
            'serial_number': self.serial_number,
        })
