from django.db import models
from django.utils.translation import ugettext_lazy as _

from . import settings as ngc_settings


class OrderSubmitRedirect(models.Model):
    cart = models.ForeignKey(ngc_settings.CART_MODEL, blank=True, null=True)
    redirect_url = models.URLField(_('Redirect URL'))
    dt = models.DateTimeField(_('DateTime'), auto_now_add=True)

    def __unicode__(self):
        return unicode(self.cart) + ' -> ' + self.redirect_url


class GoogleOrder(models.Model):
    # best practices for choices still kinda suck
    # http://www.b-list.org/weblog/2007/nov/02/handle-choices-right-way/

    # http://code.google.com/apis/checkout/developer/Google_Checkout_XML_Donation_API_Notification_API.html#tag_financial-order-state
    REVIEWING_STATE = 0
    CHARGEABLE_STATE = 1
    CHARGING_STATE = 2
    CHARGED_STATE = 3
    PAYMENT_DECLINED_STATE = 4
    CANCELLED_STATE = 5
    CANCELLED_BY_GOOGLE_STATE = 6

    STATE_CHOICES = (
        (REVIEWING_STATE, 'REVIEWING'),
        (CHARGEABLE_STATE, 'CHARGEABLE'),
        (CHARGING_STATE, 'CHARGING'),
        (CHARGED_STATE, 'CHARGED'),
        (PAYMENT_DECLINED_STATE, 'PAYMENT_DECLINED'),
        (CANCELLED_STATE, 'CANCELLED'),
        (CANCELLED_BY_GOOGLE_STATE, 'CANCELLED_BY_GOOGLE'),
    )

    @classmethod
    def trans_state_const(cls, state_string):
        for pair in cls.STATE_CHOICES:
            if pair[1] == state_string:
                return pair[0]
        return None

    # http://code.google.com/apis/checkout/developer/Google_Checkout_XML_Donation_API_Notification_API.html#Types_of_Notifications
    NEW_ORDER_NOTIFY_TYPE = 0
    ORDER_STATE_CHANGE_NOTIFY_TYPE = 1
    RISK_INFORMATION_NOTIFY_TYPE = 2
    AUTHORIZATION_AMOUNT_NOTIFY_TYPE = 3
    CHARGE_AMOUNT_NOTIFY_TYPE = 4

    NOTIFY_TYPE_CHOICES = (
        (NEW_ORDER_NOTIFY_TYPE, 'new-order-notification'),
        (ORDER_STATE_CHANGE_NOTIFY_TYPE, 'order-state-change-notification'),
        (RISK_INFORMATION_NOTIFY_TYPE, 'risk-information-notification'),
        (AUTHORIZATION_AMOUNT_NOTIFY_TYPE, 'authorization-amount-notification'),
        (CHARGE_AMOUNT_NOTIFY_TYPE, 'charge-amount-notification'),
    )

    @classmethod
    def trans_notify_type_const(cls, notify_type_string):
        for pair in cls.NOTIFY_TYPE_CHOICES:
            if pair[1] == notify_type_string:
                return pair[0]
        return None

    cart = models.ForeignKey(ngc_settings.CART_MODEL, blank=True, null=True)

    # FIXME: no PositiveBigIntegerField ?
    number = models.BigIntegerField(_('Number'), unique=True, db_index=True)
    dt_init = models.DateTimeField(_('DateTime Initialized'))
    dt_expires = models.DateTimeField(_('DateTime Expires'),
            blank=True, null=True)

    state = models.PositiveSmallIntegerField(_('State'),
            choices=STATE_CHOICES, default=REVIEWING_STATE)
    amount_charged = models.DecimalField(_('Amount Charged'),
            max_digits=8, decimal_places=2, default=0)

    last_notify_type = models.PositiveSmallIntegerField(
            _('Last Notification Type'),
            choices=NOTIFY_TYPE_CHOICES, default=NEW_ORDER_NOTIFY_TYPE)
    last_notify_dt = models.DateTimeField(
            _('Last Notification DateTime Received'))

    def __unicode__(self):
        return u'Google Order #{0}'.format(self.number)
