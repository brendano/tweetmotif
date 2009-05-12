import os,sys
dotdot = os.path.join(os.path.dirname(sys.modules[__name__].__file__), '..')
os.chdir(dotdot)
sys.path.insert(0,'')
sys.stderr = open('log/backend.log','a',0)
sys.stdout = sys.stderr

from frontend import application
