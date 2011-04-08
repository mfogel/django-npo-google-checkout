"""
Defining xpath queries used in this app.

Google Checkout API version 2.5
"""

xmlns = 'http://checkout.google.com/schema/2'

# order submit
xpq_redirect_url = '{{{0}}}redirect-url'.format(xmlns)

# notification
xpq_timestamp = '{{{0}}}timestamp'.format(xmlns)
xpq_order_number = '{{{0}}}google-order-number'.format(xmlns)
xpq_new_state = '{{{0}}}new-financial-order-state'.format(xmlns)
xpq_risk_info = '{{{0}}}risk-information'.format(xmlns)
xpq_authorization_amount = '{{{0}}}authorization-amount'.format(xmlns)
xpq_latest_charge_amount= '{{{0}}}latest-charge-amount'.format(xmlns)
xpq_total_charge_amount= '{{{0}}}total-charge-amount'.format(xmlns)
xpq_merchant_private_data = '{{{0}}}order-summary/{{{0}}}shopping-cart/{{{0}}}merchant-private-data'.format(xmlns)
xpq_good_until_date = '{{{0}}}order-summary/{{{0}}}shopping-cart/{{{0}}}cart-expiration/{{{0}}}good-until-date'.format(xmlns)
