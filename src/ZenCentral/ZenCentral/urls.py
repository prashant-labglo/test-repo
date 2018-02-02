"""
Definition of urls for ZenCentral.
"""

from datetime import datetime
from django.conf.urls import url, include
import django.contrib.auth.views

import app, app.views, app.forms
from SlideDB.urls import router as slideDbRouter
from Search.urls import router as searchRouter

from rest_framework.schemas import get_schema_view

schema_view = get_schema_view(title="SlideDB and slide search API")

# Uncomment the next lines to enable the admin:
# from django.conf.urls import include
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = [
    # Examples:
    url(r'^$', app.views.home, name='home'),
    url(r'^contact$', app.views.contact, name='contact'),
    url(r'^about', app.views.about, name='about'),
    url(r'^login/$',
        django.contrib.auth.views.login,
        {
            'template_name': 'app/login.html',
            'authentication_form': app.forms.BootstrapAuthenticationForm,
            'extra_context':
            {
                'title': 'Log in',
                'year': datetime.now().year,
            }
        },
        name='login'),
    url(r'^logout$',
        django.contrib.auth.views.logout,
        {
            'next_page': '/',
        },
        name='logout'),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),

    # SlideDB URLs
    url(r'^slidedb/', include(slideDbRouter.urls)),
    url(r'^search/', include(searchRouter.urls)),
    url('^schema$', schema_view),
]
