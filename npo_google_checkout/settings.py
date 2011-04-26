"""
Default django-npo-google-checkout settings.

All django-npo-google-checkout settings begin with the prefix 'NGC_'. For
example, a minimal configuration in your project's settings file:

NGC_CART_MODEL = 'my_shopping_cart_app.cart'
NGC_MERCHANT_ID = 42424242424242424242424242 # given to you by google checkout
NGC_MERCHANT_KEY = 'secret-key-lives-here!!' # given to you by google checkout

"""

from django.conf import settings

# NGC_BACKEND class interfaces django-npo-google-checkout to your system
# recommended to override the default with your own
BACKEND = getattr(settings, 'NGC_BACKEND',
        'npo_google_checkout.backends.default.DefaultBackend')

# Required: NGC_CART_MOOEL identifies DB model that represents your cart
CART_MODEL = settings.NGC_CART_MODEL

# NGC_MERCHANT_ID and NGC_MERCHANT_KEY must either must be defined
# in your settings.py  - OR - you can override the get_merchant_id() and
# get_merchant_key() methods in your ngc backend (useful if you're actually
# interfacing with multiple NGC accounts.
# For the tests to succeed, you have to set these in your settings.py
MERCHANT_ID = getattr(settings, 'NGC_MERCHANT_ID', None)
MERCHANT_KEY = getattr(settings, 'NGC_MERCHANT_KEY', None)

# try for NGC_HTTP_TIMEOUT seconds to connect to GC before timing out.
# on order submit redirect, user will be waiting for this real-time
HTTP_TIMEOUT = getattr(settings, 'NGC_HTTP_TIMEOUT', 5)

# make sure to override with a sandbox url during developement
# http://code.google.com/apis/checkout/developer/Google_Checkout_XML_API_Guide_for_Nonprofit_Organizations.html#integration_overview
# Note: the example curl commands in that document are wrong (as of 2011/4/5)
API_BASE_URL = getattr(settings, 'NGC_API_BASE_URL',
        'https://checkout.google.com/api/checkout/v2')

# how long we give someone to complete their checkout process
# accepted fields: 'days', 'seconds', etc.
# http://docs.python.org/library/datetime.html#datetime.timedelta
ORDER_EXPIRE = getattr(settings, 'NGC_ORDER_EXPIRE', {'days': 1})
