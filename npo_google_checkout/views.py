from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.http import Http404
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext_lazy as _
from django.views.generic import RedirectView, TemplateView

from signup_login.decorators import login_required

from .backends import get_backend

backend = get_backend(settings.NGC_BACKEND)


class OrderSubmitView(RedirectView):
    permanent = False

    def get(self, *args, **kwargs):
        return Http404(_("GET method not allowed."))

    def get_redirect_url(self, **kwagrs):
        # TODO:
        #   - use backend to get the shopping cart xml
        #   - submit sycronous API call to google (with a timeout)
        #       - if times out, redirect to error page?
        #       - else, send user to url google requests
        return None

    @method_decorator(login_required)
    def post(self, request, *args, **kwargs):
        # TODO:
        #   - extract the user's current cart using backend
        #       - verify not empty
        #       - set self.cart
        #   - send out a django signal
        return super(CartSubmitView, self).get(self, request, *args, **kwargs)


class NotificationListenerView(TemplateView):
    template_name = 'npo_google_checkout/notification_acknowledgment.html'

    def get(self, *args, **kwargs):
        return Http404(_("GET method not allowed."))

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
