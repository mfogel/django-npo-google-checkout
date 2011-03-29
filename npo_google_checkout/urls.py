from django.conf.urls.defaults import *

from .views import *

urlpatterns = patterns('',
    url(r'^order-submit/$',
        view=OrderSubmitView.as_view(),
        name='ngc-order-submit',
    ),
    url(r'^notification-listener/$',
        view=NotificationListenerView.as_view(),
        name='ngc-notification-listener',
    ),
)
