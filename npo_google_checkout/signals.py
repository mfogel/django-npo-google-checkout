from django.dispatch import Signal

order_submit = Signal(providing_args=['cart', 'redirect-url'])

notification_new_order = \
    Signal(providing_args=['cart', 'order'])

notification_order_state_change = \
    Signal(providing_args=['cart', 'order', 'old_state', 'new_state'])
notification_risk_information = \
    Signal(providing_args=['cart', 'order', 'risk_info_xml_node'])
notification_authorization_amount = \
    Signal(providing_args=['cart', 'order', 'amount'])
notification_charge_amount = \
    Signal(providing_args=['cart', 'order', 'latest_amount', 'total_amount'])
