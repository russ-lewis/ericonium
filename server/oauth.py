
import passwords

# the app is defined inside the core application file.
from ericonium import app,get_db



from flask import Flask, request, render_template, url_for, redirect, make_response, jsonify
app = Flask(__name__)



@app.route("/oauth")
def index():
    return render_template("index.html")


