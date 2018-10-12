import sys
from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy, models_committed
from sqlalchemy import event


# Print all sql statements.
import logging
logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)


SQLITE = True


def printme(text):
    print(text)
    sys.stdout.flush()


app = Flask(__name__)
if SQLITE:
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://localhost:5432/testsqlalchemysignals'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
db = SQLAlchemy(app)


if SQLITE:
    @event.listens_for(db.engine, "connect")
    def do_connect(dbapi_connection, connection_record):
        # disable pysqlite's emitting of the BEGIN statement entirely.
        # also stops it from emitting COMMIT before any DDL.
        dbapi_connection.isolation_level = None

    @event.listens_for(db.engine, "begin")
    def do_begin(conn):
        # emit our own BEGIN
        conn.execute("BEGIN")


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=False, nullable=False)
    email = db.Column(db.String(120), unique=False, nullable=False)


@models_committed.connect
def committed(*args, **kwargs):
    printme('>>> models_committed signal sent, {}, {}'.format(args, kwargs))


# @event.listens_for(db.session, 'after_commit', named=True)
# def receive_after_commit(*args, **kwargs):
#     signalling_session = kwargs['session']
#     if not signalling_session.transaction.nested:
#         printme('>>> after_commit signal sent')


# @event.listens_for(db.session, 'after_transaction_end')
# def receive_after_transaction_end(*args, **kwargs):
#     printme('>>> after_transaction_end signal sent, {}'.format(args[1].nested))


# @event.listens_for(db.engine, 'commit')
# def receive_commit(*args, **kwargs):
#     printme('>>> commit signal sent, args={} - kwargs={}'.format(args, kwargs))


# @event.listens_for(db.engine, 'after_execute')
# def receive_commit(*args, **kwargs):
#     printme('>>> after_execute signal sent, args={} - kwargs={}'.format(args, kwargs))


printme('CREATING TABLES')
db.create_all()


@app.route("/doit", methods=['GET'])
def doit():
    printme('\n\n\nSTART')
    admin = User(username='admin', email='admin@example.com')
    db.session.add(admin)

    with db.session.begin_nested():
        printme('NESTED START')
        admin = User(username='admin2', email='admin2@example.com')
        db.session.add(admin)
        printme('NESTED END')

    printme('BEFORE COMMIT')
    #db.session.commit()
    printme('END')

    return jsonify('ok')




# Create a Postgres db first:
# $ createdb testsqlalchemysignals
# Run app with:
# $ FLASK_DEBUG=true FLASK_APP=app.py flask
# Then:
# $ curl localhost:5000/doit
