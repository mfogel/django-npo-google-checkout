from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db import models
from django.utils.translation import ugettext_lazy as _


class GoogleOrder(models.Model):
    # http://code.google.com/apis/checkout/developer/Google_Checkout_XML_Donation_API_Notification_API.html#tag_financial-order-state
    STATE_CHOICES = (
        (0, 'REVIEWING'),
        (1, 'CHARGEABLE'),
        (2, 'CHARGING'),
        (3, 'CHARGED'),
        (4, 'PAYMENT_DECLINED'),
        (5, 'CANCELLED'),
        (6, 'CANCELLED_BY_GOOGLE'),
    )

    cart = models.ForeignKey(settings.NGC_CART_MODEL)
    # TODO: no PositiveBigIntegerField ?
    number = models.BigIntegerField(_('Number'))
    state = models.PositiveSmallIntegerField(_('State'),
            choices=STATE_CHOICES, default=0)
    dt_init = models.DateTimeField(_('DateTime Initialized'),
            auto_now_add=True)
    dt_state_last_changed = models.DateTimeField(
            _('DateTime State Last Changed'), auto_now_add=True)

    def __unicode__(self):
        return u'Google Order #{0}'.format(self.number)
