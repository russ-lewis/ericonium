
from flask import Flask, request, render_template, url_for, redirect, make_response, jsonify
app = Flask(__name__)

import session
app.register_blueprint(session.session_blueprint)
import oauth
app.register_blueprint(  oauth.  oauth_blueprint)




# this forces all traffic to HTTPS
@app.before_request
def force_ssl():
    if request.url.startswith("http://"):
        dest = request.url.replace("http://", "https://", 1)
        return redirect(dest, code=301)   # 301: Moved Permanently



@app.route("/")
def index():
    (sessionID, values) = session.lookup()

    assert len(values) == 1
    gmailName = values[0]

    return render_template("index.html", sessionID=sessionID, userID=gmailName)


@app.route("/game")
def game():
    (sessionID, values) = session.lookup()

    assert len(values) == 1
    gmailName = values[0]

    return render_template("game.html", sessionID=sessionID, userID=gmailName)


