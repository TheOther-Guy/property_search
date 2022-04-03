from email.errors import HeaderParseError
from django.contrib import admin
from .models import Feature, Melissa, Head


# Register your models here.
    
admin.site.register(Feature)
admin.site.register(Head)
admin.site.register(Melissa)


