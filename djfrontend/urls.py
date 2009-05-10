from django.conf.urls.defaults import *

import os
dir = os.path.abspath(os.path.dirname(__file__))

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',

  (r'^', include('djfrontend.twi.urls')),
  (r'^static/(?P<path>.*)$', 'django.views.static.serve', {'document_root': os.path.join(dir,'static')}),
  (r'^about$', 'django.views.generic.simple.direct_to_template', {'template':'about.tpl'})
  
  # Example:
  # (r'^twidjango/', include('twidjango.foo.urls')),

  # Uncomment the admin/doc line below and add 'django.contrib.admindocs' 
  # to INSTALLED_APPS to enable admin documentation:
  # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

  # Uncomment the next line to enable the admin:
  # (r'^admin/(.*)', admin.site.root),
)
