"""
Ensure settings required by NGC are correctly defined.

Define some NGC-specific constants.
"""

from django.conf import settings

if not settings.NGC_BACKEND:
    raise ImproperlyConfigured("You must specify in your django settings the ngo-google-checkout backend to use using NGC_BACKEND")

if not settings.NGC_CART_MODEL:
    raise ImproperlyConfigured("You must specify in your django settings the name of your cart in your database using NGC_CART_MODEL")

if not settings.NGC_MERCHANT_ID:
    raise ImproperlyConfigured("You must specify in your django settings the merchant_id to use with google checkout using NGC_MERCHANT_ID")

if not settings.NGC_MERCHANT_KEY:
    raise ImproperlyConfigured("You must specify in your django settings the merchant_key to use with google checkout using NGC_MERCHANT_KEY")

if not settings.NGC_API_BASE_URL:
    raise ImproperlyConfigured("You must specify in your django settings the base url of the google checkout to use using NGC_API_BASE_URL")


NGC_ORDER_SUBMIT_URL = '{0}Donations/{1}'.format(
        settings.NGC_API_BASE_URL, settings.NGC_MERCHANT_ID)
