"""
thsutton's approach to application-specfic default settings, with
minor modifications.
https://github.com/thsutton/django-application-settings/
"""

# NGC_BACKEND class interfaces django-npo-google-checkout to your system
# recommended to override the default with your own
NGC_BACKEND = 'npo_google_checkout.backends.default.DefaultBackend'

# Required: NGC_CART_MOOEL identifies DB model that represents your cart
NGC_CART_MODEL = None

# Required: google checkout provides you want a merchant id & key
NGC_MERCHANT_ID = None
NGC_MERCHANT_KEY = None

# try for NGC_HTTP_TIMEOUT seconds to connect to GC before timing out.
# on order submit redirect, user will be waiting for this real-time
NGC_HTTP_TIMEOUT = 5

# make sure to override with a sandbox url during developement
# http://code.google.com/apis/checkout/developer/Google_Checkout_XML_API_Guide_for_Nonprofit_Organizations.html#integration_overview
# Note: the example curl commands in that document are wrong (as of 2011/4/5)
NGC_API_BASE_URL = \
    'https://checkout.google.com/api/checkout/v2/request/Merchant'
