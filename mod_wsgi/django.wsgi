import os,sys
dotdot = os.path.join(os.path.dirname(sys.modules[__name__].__file__), '..')
os.chdir(dotdot)
sys.path.append('')
sys.stderr = open('log/djfrontend.log','a',0)
sys.stdout = sys.stderr
os.environ['DJANGO_SETTINGS_MODULE'] = 'djfrontend.settings'
import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()

