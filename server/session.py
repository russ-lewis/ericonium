# SESSION HANDLING
#
# This is a Flask "blueprint" (that is, a sub-module), which can be imported
# into various functions.  You include it into a Flask application with:
#     import session
#     app.register_blueprint(session.session_blueprint)
# https://flask.palletsprojects.com/en/1.0.x/blueprints/
#
# This module assumes the following:
#   - That there is a module named 'db', which includes a function, get_db(),
#     which will return a connection to a database (using the MySQLdb library
#     or similar).  (get_db() should have already connected to the correct DB
#     inside the instance.)
#   - That the database contains a table 'sessions', which has (at least) the
#     following fields:
#       id         CHAR(32)
#       expiration DATETIME
#     Plus, one or more "value" fields.  The two fields above are assumed to
#     NOT NULL; all other fields (which may or may not be specified in the
#     "value" list) must have default values, because we won't set them by
#     default.
#
# This module also includes some config constants.  We provide good defaults,
# but your code may override them:
#     SESSION_TIMEOUT, AGING_TIMEOUT : Two times, given in hh:mm:ss format,
#         which speciy (a) who long a session will live until it expires; and
#         (b) how old a session needs to be before we will automatically
#         refresh it (so that it doesn't later expire)
#
#     COOKIE_MAX_AGE : How long cookies should be stored by the browser (in
#         seconds)
#
#    VALUE_FIELDS : a comma-separated list of strings, which are the
#         fields to store in the 'session' table in the DB.  These are queried
#         when we look up the session ID; if the session ID is valid (and not
#         expired), then these fields are read in the same SELECT statement.
#         These values are returned from lookup(); the second return value is
#         a list of the same length (with None for values that were NULL in
#         the database).
#
# If code wants to update a value associated with a given value field of the
# session, call set_session_value().  This will perform a DB operation to
# set the requested field, on the appropriate session in the database.
#



import random



from flask import Blueprint, request
session_blueprint = Blueprint("session", __name__)

from db        import get_db



SESSION_TIMEOUT = "00:30:00"    # 30 minutes
AGING_TIMEOUT   = "00:15:00"    # 15 minutes
COOKIE_MAX_AGE  = 1800          # 30 minutes, as well

VALUE_FIELDS = ["gmailName"]



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
    cursor.execute("""SELECT """+ ",".join(VALUE_FIELDS) +""" ,
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

    values =     rows[0][:-1]
    aging  = int(rows[0][ -1])

    if aging == 1:
        _update_expiration(db, sessionID)

    return (sessionID, values)



# create a brand-new session.  Return the proper tuple: new session ID, and
# then all other fields are None.
def _create(db):
    sessionID = ("%032x" % random.getrandbits(128))

    cursor = db.cursor()
    cursor.execute("INSERT INTO sessions(id,expiration) VALUES(%s,ADDTIME(NOW(),%s));", (sessionID, SESSION_TIMEOUT));
    rowcount = cursor.rowcount
    cursor.close()
    db.commit()        # TODO: should I defer this until some common code, later?

    # error state.  TODO: better handling?
    assert rowcount == 1


    # record that we need to set the cookie, when this request terminates.
    request.session_set_sessionID = sessionID

    # normal pass - a new session was created
    return (sessionID, [None]*len(VALUE_FIELDS))



def _update_expiration(db, sessionID):
    cursor = db.cursor()
    cursor.execute("UPDATE sessions SET expiration=ADDTIME(NOW(),%s) WHERE id=%s;", (SESSION_TIMEOUT, sessionID))
    cursor.close()   # we don't confirm that this works.  We just hope.

    db.commit()        # TODO: should I defer this until some common code, later?

    # record that we need to (re)set the cookie, when this request terminates.
    request.session_set_sessionID = sessionID



def set_session_value(sessionID, fieldName, value):
    db = get_db()

    cursor = db.cursor()
    cursor.execute("UPDATE sessions SET "+fieldName+"=%s WHERE id=%s", (value, sessionID))
    rowcount = cursor.rowcount()
    cursor.close()

    db.commit()    # TODO: should I defer this until later???



@session_blueprint.after_request
def cookie_check(resp):
    if "session_set_sessionID" in dir(request):
        resp.set_cookie("sessionID", request.session_set_sessionID,
                        max_age = COOKIE_MAX_AGE)
    return resp


