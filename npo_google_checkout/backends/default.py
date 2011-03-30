from django.template import Context, Template
from django.utils.safestring import mark_safe


class DefaultBackend(object):
    """
    Default NGC backend.
    Recommended to inherit from this object and override methods as
    desired.
    """

    def get_order_submit_xml(self, cart_id):
        """
        http://code.google.com/apis/checkout/developer/Google_Checkout_XML_API_Guide_for_Nonprofit_Organizations.html#create_checkout_cart
        """
        template = self._get_order_submit_template(cart_id)
        context = self._get_order_submit_context(cart_id)
        return unicode(template.render(context))

    def get_edit_cart_url(self, cart_id):
        """
        Where GC should send the user to edit their existing cart.
        http://code.google.com/apis/checkout/developer/Google_Checkout_XML_Donation_API_Tag_Reference.html#tag_edit-cart-url
        """
        return None

    def get_continue_shopping_url(self, cart_id):
        """
        Where GC should send the user when they're done with the checkout.
        http://code.google.com/apis/checkout/developer/Google_Checkout_XML_Donation_API_Tag_Reference.html#tag_continue-shopping-url
        """
        return None

    def get_active_cart_id(self, user):
        """
        Return the id of the user's currently active shopping cart.
        Assumes user can only have one active shopping cart at a time.
        """
        return None

    def _get_shopping_cart_xml(self, cart_id):
        """
        The shopping cart GC should present the user for review.
        http://code.google.com/apis/checkout/developer/Google_Checkout_XML_Donation_API_Tag_Reference.html#tag_shopping-cart

        Carts must contain at least one item.
        """
        xml = u"""
            <items>
                <item>
                    <item-name>example item name</item-name>
                    <item-description>example item desc</item-description>
                    <unit-price currency="USD">1.01</unit-price>
                    <quantity>42</quantity>
                </item>
            </items>
        """
        return mark_safe(xml)


    def _get_order_submit_context(self, cart_id):
        return Context({
                'cs_url': self.get_continue_shopping_url(cart_id),
                'ec_url': self.get_edit_cart_url(cart_id),
                'shopping_cart': self._get_shopping_cart_xml(cart_id),
            })

    ORDER_SUBMIT_TEMPLATE_STR = """{% spaceless %}
        <?xml version="1.0" encoding="UTF-8"?>
        <checkout-shopping-cart xmlns="http://checkout.google.com/schema/2">
            <shopping-cart>{{ shopping_cart|default:'' }}</shopping-cart>
            <checkout-flow-support>
                <merchant-checkout-flow-support>
                    {% if cs_url %}<continue-shopping-url>{{ cs_url }}</continue-shopping-url>{% endif %}
                    {% if ec_url %}<edit-cart-url>{{ ec_url }}</edit-cart-url>{% endif %}
                </merchant-checkout-flow-support>
            </checkout-flow-support>
        </checkout-shopping-cart>
    {% endspaceless %}"""

    def _get_order_submit_template(self, cart_id):
        return Template(self.ORDER_SUBMIT_TEMPLATE_STR)
