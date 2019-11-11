
import MySQLdb
import passwords    # my private password file

from flask import request



def get_db():
    if "db_conn" not in dir(request):
        request.db_conn = MySQLdb.connect(host   = passwords.SQL_HOST,
                                          user   = passwords.SQL_USER,
                                          passwd = passwords.SQL_PASSWD,
                                          db     = "ericonium")
    return request.db_conn



# TODO: add an @app.after_request() call, which will commit if necessary.
#       drive it with a queue_commit() call in this function, which sets a
#       flag in the request object (see the after_request() in session.py)


