import sys
import os


APP_DIR = "/home/ec2-user/ericonium/server/"

# why doesn't WSGI set this up automatically?  I find the next two steps
# fairly annoying!
sys.path.insert(0, APP_DIR)
os.chdir(APP_DIR)


from ericonium_control_plane import app as application

