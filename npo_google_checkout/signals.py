from django.dispatch import Signal

order_submit = Signal(providing_args=['redirect-url'])

# TODO: add a whole bunch of notification signals
