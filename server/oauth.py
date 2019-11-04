
import passwords

# the app is defined inside the core application file.
from ericonium import app,get_db
import session



from flask import Flask, request, render_template, url_for, redirect, make_response, jsonify
app = Flask(__name__)



OAUTH_CALLBACK_URL = "https://userid-associator-dot-lecturer-russ.appspot.com/oauth_callback/"



@app.route("/")
def index():
    if DISABLED:
        return render_template("disabled.html")

    db = pnsdp.open_db()
    (sessionID,new_session, netID,github,google) = session_lookup(db)

    return cookie_check(sessionID, new_session,
                        render_template("index.html",
                                        netID  = netID,
                                        github = github,
                                        google = google))


