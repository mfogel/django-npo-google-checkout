"""
Using thsutton's approach to application-specfic default settings.
https://github.com/thsutton/django-application-settings/

Required settings logic is my own.
"""

from django.conf import settings

required_settings = {
        'NGC_BACKEND': 'which google-checkout backend to use',
        'NGC_CART_MODEL': 'name of the model of your cart in your database',
        'NGC_MERCHANT_ID': 'the merchant_id google checkout gave you',
        'NGC_MERCHANT_KEY': 'the merchant_key google checkout gave you',
    }

for k, v in required_settings.iteritems():
    if not hasattr(settings, k):
        raise Improperly(
                "Required setting '{0}' (for {1}) not found.".format(k,v))

# make sure to override with a sandbox url during developement
# http://code.google.com/apis/checkout/developer/Google_Checkout_XML_API_Guide_for_Nonprofit_Organizations.html#integration_overview
# Note: the example curl commands in that document are wrong (as of 2011/4/5)
NGC_API_BASE_URL = \
    'https://checkout.google.com/api/checkout/v2/request/Merchant/'

NGC_ORDER_SUBMIT_URL = \
    '{0}Donations/{1}'.format(
        settings.NGC_API_BASE_URL, settings.NGC_MERCHANT_ID)
