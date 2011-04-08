from datetime import datetime, timedelta

from django.conf import settings
from django.template import Context, Template
from django.utils.safestring import mark_safe


class DefaultBackend(object):
    """
    Default handling of order submission.
    Recommended to inherit from this class and override methods as
    desired.
    """

    def __init__(self, request, private_data=None):
        super(DefaultBackend, self).__init__()
        self.request = request
        self.private_data = private_data

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
        expire_delta = timedelta(**settings.NGC_ORDER_EXPIRE)
        utc_expire = utc_now + expire_delta
        str_rep = utc_expire.replace(microsecond=0).isoformat() + 'Z'
        return str_rep

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

    def _get_merchant_private_data(self):
        """
        Default implementation: merchant private data used to tie a
        google order number to a specific instance of your checkout
        system's cart.
        """
        return self.private_data

    def _get_order_submit_context(self):
        return Context({
                'cs_url': self.get_continue_shopping_url(),
                'ec_url': self.get_edit_cart_url(),
                'cart_expiration': self.get_cart_expiration(),
                'items_xml': self._get_items_xml(),
                'private_data': self._get_merchant_private_data(),
            })

    ORDER_SUBMIT_TEMPLATE_STR = """{% spaceless %}
        <?xml version="1.0" encoding="UTF-8"?>
        <checkout-shopping-cart xmlns="http://checkout.google.com/schema/2">
            <shopping-cart>
                {{ items_xml }}
                {% if private_data %}<merchant-private-data>{{ private_data }}</merchant-private-data>{% endif %}
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
