
from unicodedata import name
from django.contrib import admin
from django.urls import path
from . import views
# path converters
# int: numbers
# str: strings
# path: whole path
# slug: hyphen and underscores
# UUID: universally unique identifier like user number

urlpatterns = [
    path('', views.index, name='home'),
    path('epa.html', views.epa, name='epa'),
    path('fema.html', views.fema, name='fema'),
    path('melissa.html', views.melissa, name='melissa'),
    path('map.html', views.map, name='map'),
    path('register.html', views.register, name='register'),
    path('login.html', views.Login, name='Login'),
    path('Logout', views.Logout, name='Logout'),
    
    
    ]