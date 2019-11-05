
# the app is defined inside the core application file.
from ericonium import app,get_db



from flask import Flask, request, render_template, url_for, redirect, make_response, jsonify
app = Flask(__name__)



def get_db():
    if "db_conn" not in dir(request):
        request.db_conn = MySQLdb.connect(host   = passwords.SQL_HOST,
                                          user   = passwords.SQL_USER,
                                          passwd = passwords.SQL_PASSWD,
                                          db     = "ericonium")
    return request.db_conn



@app.route("/config")
def index():
    return render_template("index.html")

