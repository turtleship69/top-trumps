from threading import Lock
import os, uuid
from random import randint
from flask import Flask, send_from_directory, render_template, request, make_response, session, redirect, copy_current_request_context
from flask_socketio import SocketIO, emit, join_room, leave_room, close_room, rooms, disconnect
from flask_session import Session
from pprint import pprint

app = Flask('app')
app.config['SECRET_KEY'] = os.urandom(64)
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_FILE_DIR'] = './.flask_session/'
async_mode = None
socketio = SocketIO(app, async_mode=async_mode)
thread = None
thread_lock = Lock()
Session(app)

queue, players = {}, {}

global pins
pins = []
def pin():
    flag = False
    while not flag:
        pin = randint(100000, 999999)
        global pins
        if not pin in pins:
            pins.append(pin)
            flag = True
    return pin

@app.route('/')
def hello_world():
    print("players: ")
    pprint(players)
    print("queue: ")
    pprint(queue)
    return render_template("home.html")

#hosting
@app.route('/host', methods=['POST', 'GET'])
def host():
    if not session.get('uuid'):
        # Step 1. Visitor is unknown, give random ID
        session['uuid'] = str(uuid.uuid4())
        players[session.get('uuid')] = {"room": pin(), "username": "", "score": 0, "role": "host"}
        print(players[session.get('uuid')])
    # Step 4. Signed in, display data
    try:
        room = players[session.get('uuid')]["room"]
    except:
        players[session.get('uuid')] = {"room": pin(), "username": "", "score": 0, "role": "host"}
        room = players[session.get('uuid')]["room"]
    queue[str(room)]={"host":session.get('uuid')}
    print(queue)
    print(players)
    return render_template("hostSignedIn.html", room=room, uuid = session.get('uuid'), domain = request.headers['Host'], async_mode=socketio.async_mode)


#joining
@app.route('/join', methods=['POST', 'GET'])
def joinpage():
    """
    check if user has uuid in session, if not assign one
    check url arguments for pin, if present set pin varible to it
    if not present, ask user for pin
    return joinRoom.html template with pin (and uuid as necessary) 
    """
    #check if request method is get
    if request.method == 'GET':
        if not session.get('uuid'):
            # Step 1. Visitor is unknown, give random ID
            session['uuid'] = str(uuid.uuid4())
        # Step 4. Signed in, display data
        try:
            room = request.args.get('roomID')
        except:
            room = None
        if room:
            return render_template("joinRoom.html", room=room)
        else:
            return render_template("joinRoom.html")
    else:
        try: 
            queue[request.form.get('roomID')]["players"].append(session.get('uuid'))
        except KeyError:
            queue[request.form.get('roomID')]["players"] = [session.get('uuid')]
        print(session.get("uuid"))
        players[session.get('uuid')] = {"room": request.form.get('roomID'), "username": request.form.get('username'), "score": 0, "role": "player"}
        room = request.form.get('roomID')
        socketio.emit('queue_update', {'data': queue[str(room)]}, to=room)
        return render_template("joinedRoom.html", room=request.form.get("roomID"), uuid=session.get('uuid'), username=request.form.get('username'))

#start game
@app.route('/start', methods=['POST', 'GET'])
def start():
    return "hello"
    # room = request.args.get('pin')
    # queue[str(room)]["host"] = session.get('uuid')
    # queue[str(room)]["player"] = session.get('uuid')
    # return render_template("start.html", room=room, async_mode=socketio.async_mode)






            
#Socket
@socketio.event
def connect():
    emit('my_response', {'data': 'Connected', 'count': 0})

@socketio.event
def join(message):
    join_room(message['room'])
    print(message['uuid'], "connected to " + message['room'])
    emit('my_response', queue)





#run server and beautify website
@app.route('/web/<path:path>')
def web(path):
    return send_from_directory('web', path)

@app.route('/favicon.ico')
def ico():
    return send_from_directory('web', 'favicon.ico')

app.run(host='0.0.0.0', port=8080)