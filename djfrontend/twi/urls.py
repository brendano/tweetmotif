from django.conf.urls.defaults import *

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('djfrontend.twi.views',

    url(r'^do_query$', "do_query"),
    url(r'^search/(?P<query>.*)/$', "show_results"),
    url(r'^$', "index"),
    url(r'^about$', "about"),
    
    url(r'^.*$', "common_user_error"),

    # Example:
    # (r'^twidjango/', include('twidjango.foo.urls')),

    # Uncomment the admin/doc line below and add 'django.contrib.admindocs' 
    # to INSTALLED_APPS to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # (r'^admin/(.*)', admin.site.root),
)
