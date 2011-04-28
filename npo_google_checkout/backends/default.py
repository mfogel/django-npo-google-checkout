from datetime import datetime, timedelta

from django.template import Context, Template
from django.utils.safestring import mark_safe

from .. import settings as ngc_settings
from ..xpath import xpq_merchant_private_data


class DefaultBackend(object):
    """
    Default handling of order submission.
    Recommended to inherit from this class and override methods as
    desired.
    """
    notify_xml = None
    private_data = None

    def __init__(self, request, notify_xml=None):
        super(DefaultBackend, self).__init__()
        self.request = request
        if notify_xml:
            self.notify_xml = notify_xml
            mpd = notify_xml.findtext(xpq_merchant_private_data)
            self.private_data = self._decode(mpd) if mpd else None

    def get_merchant_id(self):
        return ngc_settings.MERCHANT_ID

    def get_merchant_key(self):
        return ngc_settings.MERCHANT_KEY

    def get_cart(self):
        """
        Use self.private_data and self.request to access the user's cart.
        """
        return None

    def get_order_submit_xml(self):
        """
        http://code.google.com/apis/checkout/developer/Google_Checkout_XML_API_Guide_for_Nonprofit_Organizations.html#create_checkout_cart
        """
        template = self._get_order_submit_template()
        context = self._get_order_submit_context()
        return unicode(template.render(context))

    def get_edit_cart_url(self):
        """
        Where GC should send the user to edit their existing cart.
        http://code.google.com/apis/checkout/developer/Google_Checkout_XML_Donation_API_Tag_Reference.html#tag_edit-cart-url
        """
        return None

    def get_continue_shopping_url(self):
        """
        Where GC should send the user when they're done with the checkout.
        http://code.google.com/apis/checkout/developer/Google_Checkout_XML_Donation_API_Tag_Reference.html#tag_continue-shopping-url
        """
        return None

    def get_cart_expiration(self):
        """
        When GC should expire the given cart.
        http://code.google.com/apis/checkout/developer/Google_Checkout_XML_Donation_API_Notification_API.html#tag_good-until-date
        By default, return now + NGC_ORDER_EXPIRE in a format google can take
        """

        """Extract the timestamp, converted to the local timezone"""
        utc_now = datetime.utcnow()
        expire_delta = timedelta(**ngc_settings.ORDER_EXPIRE)
        utc_expire = utc_now + expire_delta
        str_rep = utc_expire.replace(microsecond=0).isoformat() + 'Z'
        return str_rep

    _encoding_prefix = 'ngc::'

    def _encode(self, private):
        """
        Encode the private value. Inteded for use with merchant-private-data.
        """
        return self._encoding_prefix + str(private)

    def _decode(self, encoded):
        """
        Decode the encoded value. Inteded for use with merchant-private-data.
        """
        if not encoded.startswith(self._encoding_prefix):
            return None
        return encoded[len(self._encoding_prefix):]

    def _get_items_xml(self):
        """
        The items in the shopping cart GC should present the user for review.
        http://code.google.com/apis/checkout/developer/Google_Checkout_XML_Donation_API_Tag_Reference.html#tag_shopping-cart

        Carts must contain at least one item.
        """
        xml = u"""
            <items>
                <item>
                    <item-name>example item name</item-name>
                    <item-description>example item desc</item-description>
                    <unit-price currency="USD">42.42</unit-price>
                    <quantity>1</quantity>
                </item>
            </items>
        """
        return mark_safe(xml)

    def _get_order_submit_context(self):
        return Context({
                'cs_url': self.get_continue_shopping_url(),
                'ec_url': self.get_edit_cart_url(),
                'cart_expiration': self.get_cart_expiration(),
                'items_xml': self._get_items_xml(),
                'merchant_private_data': self._encode(self.private_data),
            })

    ORDER_SUBMIT_TEMPLATE_STR = """{% spaceless %}
        <?xml version="1.0" encoding="UTF-8"?>
        <checkout-shopping-cart xmlns="http://checkout.google.com/schema/2">
            <shopping-cart>
                {{ items_xml }}
                {% if merchant_private_data %}<merchant-private-data>{{ merchant_private_data }}</merchant-private-data>{% endif %}
                {% if cart_expiration %}<cart-expiration><good-until-date>{{ cart_expiration }}</good-until-date></cart-expiration>{% endif %}
            </shopping-cart>
            <checkout-flow-support>
                <merchant-checkout-flow-support>
                    {% if cs_url %}<continue-shopping-url>{{ cs_url }}</continue-shopping-url>{% endif %}
                    {% if ec_url %}<edit-cart-url>{{ ec_url }}</edit-cart-url>{% endif %}
                </merchant-checkout-flow-support>
            </checkout-flow-support>
        </checkout-shopping-cart>
    {% endspaceless %}"""

    def _get_order_submit_template(self):
        return Template(self.ORDER_SUBMIT_TEMPLATE_STR)
