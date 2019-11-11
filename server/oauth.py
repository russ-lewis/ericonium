
import random
import urllib

from flask import Blueprint, request, url_for
oauth_blueprint = Blueprint("oauth", __name__)

import session
import db

import passwords    # for the OAUTH secrets and such



SESSION_TIMEOUT = "00:30:00"    # 30 minutes



@oauth_blueprint.route("/oauth/login")
def login():
    # look up the session ID.
    (sessionID, value_fields) = session.lookup()

    assert len(value_fields) == 1
    gmailName = value_fields[0]


    # print("login(): sessionID=%s" % sessionID)

    # does the login already exist?  If so, just redirect back to the index
    # page, with no message to the user.  It's just "done", immediately.
    if gmailName is not None:
        return redirect(url_for("index"), code=302)


    # create the nonce for the OAuth process, and record it into the DB
    nonce = ("%032x" % random.getrandbits(128))

    # print("login(): nonce=%s" % nonce)

    # record the ongoing login attempt to the database 
    conn = db.get_db()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO oauth_login_states(nonce,expiration,sessionID) VALUES(%s,ADDTIME(NOW(),%s),%s);", (nonce,SESSION_TIMEOUT,sessionID));
    count = cursor.rowcount
    cursor.close()
    conn.commit()

    # print("login(): update count=%s" % count)

    if count != 1:
        return render_template("error.html", message="Internal error, could not create a new login process.")


    # compose the redirect to the service.  Most of the variables are
    # service-specific, although the 'state' variable is common, since it's a
    # standard part of the protocol.
    #
    # Some of these parameters are public, and so I set them with code here.
    # Others are private, so they are taken from the passwords file.

    oauth_url = "https://accounts.google.com/o/oauth2/v2/auth"
    client_id = passwords.GOOGLE_ERICONIUM_OAUTH_CLIENT_ID
    scope     = "email"
    state     = nonce

    # NOTE:
    #
    # response_type is required for NetID, but not for GitHub.  I haven't yet
    # re-tested the GitHub flow with it; hopefully, it's ignored.
    url = "%s?%s" % (
                oauth_url,
                urllib.urlencode({"client_id"    : client_id,
                                        "redirect_url" : url_for("oauth.callback"),
                                        "redirect_uri" : url_for("oauth.callback"),
                                        "response_type": "code",
                                        "scope"        : scope,
                                        "access_type"  : "online",
                                        "state"        : state,})
            )

    # print("login(): redirect url=%s" % url)

    return url
    #return redirect(url, code=302)



@oauth_blueprint.route("/oauth/callback/")
def callback():
    # TODO: handle the 'error' variable

    if "code" not in request.values or "state" not in request.values:
        return render_template("error.html", message="The OAuth callback has invalid HTTP parameters")
    code  = request.values["code"]
    state = request.values["state"]


    # connect to the database, and check the cookie state.
    (sessionID, ignored) = session.lookup()


    # look up the login nonce, and compare it to the oauth_login_states table.
    # We'll do so twice, once without expiration checks, and once *WITH*,
    # so that we'll be able to give good error messages to the user.
    conn = db.get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM oauth_login_states WHERE nonce=%s AND sessionID=%s;", (state,sessionID))
    tmp1 = cursor.fetchall()
    cursor.close()

    cursor = conn.cursor()
    cursor.execute("SELECT * FROM oauth_login_states WHERE nonce=%s AND sessionID=%s AND NOW()<expiration;", (state,sessionID))
    tmp2 = cursor.fetchall()
    cursor.close()

    cursor = conn.cursor()
    cursor.execute("DELETE FROM oauth_login_states WHERE nonce=%s AND sessionID=%s;", (state,sessionID))
    cursor.close()
    conn.commit()

    # print("oauth_callback(): len(tmp1)=%d len(tmp2)=%d" % (len(tmp1), len(tmp2)))

    if len(tmp1) == 0:
        return render_template("error.html", message="Invalid 'state' variable in the OAuth callback.")
    if len(tmp2) == 0:
        return render_template("error.html", message="The login process has expired.")


    # exchange the code for the real token.
    #
    # 'code' and 'state' are both taken from the form variables above
    token_url     = "https://www.googleapis.com/oauth2/v4/token"
    client_id     = passwords.GOOGLE_ERICONIUM_OAUTH_CLIENT_ID
    client_secret = passwords.GOOGLE_ERICONIUM_OAUTH_CLIENT_SECRET

    post_form_variables = {"client_id"     : client_id,
                           "client_secret" : client_secret,
                           "code"          : code,
                           "redirect_url"  : url_for("/oauth/callback"),
                           "redirect_uri"  : url_for("/oauth/callback"),
                           "state"         : state,
                           "grant_type"    : "authorization_code",}

    # print("oauth_callback(): access_token url=%s" % url)


    # we composed the URL above.  Now we are going to actually connect to the
    # service and convert the 'code' into an 'access_token'
    resp = requests.post(token_url, data=post_form_variables)
    token = None

#    if service != "netID":
#        return render_template("debug.html", more=("%s\n\n%s\n\n%s" % (token_url,post_form_variables,resp.text)))


    # parse the output returned by the POST operation

    if resp.status_code != 200:
        return render_template("error.html", message="The HTTP status code from the code->token POST operation was not was expected.  Expected: 200  Actual: %d" % resp.status_code)

    if resp.headers["content-type"].split(';')[0] != "application/json":
        return render_template("error.html", message="The reponse from the code->token POST operation was not was expected.  Expected: application/json  Actual: %s" % resp.headers["content-type"])

    reply = json.loads(resp.text)
    if "access_token" not in reply:
        return render_template("error.html", message="The reponse from the code->token POST operation was not was expected.  No 'access_token' field was found.")

    token = reply["access_token"]

    # print("oauth_callback(): token=%s" % token)

    if token is None:
        return render_template("error.html", message="Access_token not provided in the OAuth callback.")


    # now, use the access_token to go get the user ID for this user.
    login_resp = requests.get("https://openidconnect.googleapis.com/v1/userinfo",
                              headers={"Authorization": "Bearer "+token})
    service_id = json.loads(login_resp.text.encode("utf-8"))["email"]


    # record the gmailName; associate it with this sesssion.
    session.set_value_field("gmailName", service_id)


    # now that we're done, redirect back to the main page.
    return redirect(url_for("index"), code=302)



