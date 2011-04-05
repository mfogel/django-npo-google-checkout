from django.contrib import admin

from .models import *

admin.site.register((OrderSubmitRedirect,))
admin.site.register((GoogleOrder,))
