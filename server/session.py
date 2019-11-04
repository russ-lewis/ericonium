
import random



from flask import Flask, request, render_template, url_for, redirect, make_response, jsonify

# the app is defined inside the core application file.
from ericonium import app,get_db



SESSION_TIMEOUT = "00:30:00"    # 30 minutes
AGING_TIMEOUT   = "00:15:00"    # 15 minutes
COOKIE_MAX_AGE  = 1800          # 30 minutes, as well



# utility func: look up the cookie (if it exists), and then look up the
# various user IDs associated with it (if any).  The first value returned
# is actually the *new* session ID (if one is created), or None if an
# ongoing session already exists.
def lookup():
    db = get_db()

    if "sessionID" not in request.cookies:
        return _create(db)

    sessionID = request.cookies["sessionID"]

    cursor = db.cursor()
    cursor.execute("""SELECT gmailName,
                             CASE WHEN ADDTIME(NOW(),%s)>expiration THEN 1
                                  ELSE                                   0
                                  END AS is_aging
                        FROM sessions
                       WHERE id=%s AND NOW()<expiration;""", (AGING_TIMEOUT, sessionID))
    rows = cursor.fetchall()
    cursor.close()

    assert len(rows) <= 1
    if len(rows) == 0:
        return _create(db)

    gmailName =     rows[0][0]
    aging     = int(rows[0][1])

    if aging == 1:
        _update_expiration(db, sessionID)

    return (aging, gmailName)



# create a brand-new session.  Return the proper tuple: new session ID, and
# then all other fields are None.
def _create(db):
    sessionID = ("%032x" % random.getrandbits(128))

    cursor = db.cursor()
    cursor.execute("INSERT INTO sessions(id,expiration) VALUES(%s,ADDTIME(NOW(),%s));", (sessionID, SESSION_TIMEOUT));
    rowcount = cursor.rowcount
    cursor.close()
    db.commit()        # TODO: should I defer this until some common code, later?

    # error state
    if rowcount != 1:
        return (None,None)


    # record that we need to set the cookie, when this request terminates.
    request.session_set_sessionID = sessionID

    # normal pass - a new session was created
    return (sessionID, None)



def _update_expiration(db, sessionID):
    cursor = db.cursor()
    cursor.execute("UPDATE sessions SET expiration=ADDTIME(NOW(),%s) WHERE id=%s;", (SESSION_TIMEOUT, sessionID))
    cursor.close()   # we don't confirm that this works.  We just hope.

    db.commit()        # TODO: should I defer this until some common code, later?

    # record that we need to (re)set the cookie, when this request terminates.
    request.session_set_sessionID = sessionID



@app.after_request
def cookie_check(resp):
    if "session_set_sessionID" in dir(request):
        resp.set_cookie("sessionID", request.session_set_sessionID,
                        max_age = COOKIE_MAX_AGE)
    return resp


