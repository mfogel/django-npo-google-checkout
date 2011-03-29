from django.template import Context, Template


class DefaultBackend(object):
    """
    Default NGC backend.
    Recommended to inherit from this object and override methods as
    desired.
    """

    def get_checkout_shopping_cart_xml(self, cart_id):
        """
        http://code.google.com/apis/checkout/developer/Google_Checkout_XML_API_Guide_for_Nonprofit_Organizations.html#create_checkout_cart
        """
        self.cart_id = cart_id
        template = self._get_cart_submit_template()
        context = self._get_cart_submit_context()
        return template.render(context)

    def get_shopping_cart_xml(self):
        """
        The shopping cart GC should present the user for review.
        http://code.google.com/apis/checkout/developer/Google_Checkout_XML_Donation_API_Tag_Reference.html#tag_shopping-cart
        """
        return None

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

    def _get_checkout_shopping_cart_context(self):
        return Context({
                'cs_url': self.get_continue_shopping_url(),
                'ec_url': self.get_edit_cart_url(),
                'shopping_cart': self.get_shopping_cart_xml(),
            })

    CART_SUBMIT_TEMPLATE_STR = """
        <checkout-shopping-cart xmlns="http://checkout.google.com/schema/2">
            {% if shopping_cart %}<shopping-cart>{{ shopping_cart }}</shopping-cart>{% endif %}
            <merchant-checkout-flow-support>
                {% if cs_url %}<continue-shopping-url>{{ cs_url }}</continue-shopping-url>{% endif %}
                {% if ec_url %}<edit-cart-url>{{ ec_url }}</edit-cart-url>{% endif %}
            </merchant-checkout-flow-support>
        </checkout-shopping-cart>
    """

    def _get_checkout_shopping_template(self):
        return Template(self.CART_SUBMIT_TEMPLATE_STR)
