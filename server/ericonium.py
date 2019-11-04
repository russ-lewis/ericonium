
import json
import MySQLdb

import passwords



from flask import Flask, request, render_template, url_for, redirect, make_response, jsonify
app = Flask(__name__)



def get_db():
    if "db_conn" not in dir(request):
        request.db_conn = MySQLdb.connect(host   = passwords.SQL_HOST,
                                          user   = passwords.SQL_USER,
                                          passwd = passwords.SQL_PASSWD,
                                          db     = "ericonium")
    return request.db_conn



# these are subcomponents of the Ericonium application
import oauth
import config_plane



# this forces all traffic to HTTPS
@app.before_request
def force_ssl():
    if request.url.startswith("http://"):
        dest = request.url.replace("http://", "https://", 1)
        return redirect(dest, code=301)   # 301: Moved Permanently



@app.route("/")
def index():
    return render_template("index.html")


