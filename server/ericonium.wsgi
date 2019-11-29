import sys
import os


APP_DIR = os.path.dirname(__file__)

# why doesn't WSGI set this up automatically?  I find the next two steps
# fairly annoying!
sys.path.insert(0, APP_DIR)
os.chdir(APP_DIR)


from ericonium import app as application

