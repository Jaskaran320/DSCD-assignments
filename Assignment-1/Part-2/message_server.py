import time
import zmq
import json
import threading

context = zmq.Context()
registration_req_socket = context.socket(zmq.REP)
registration_req_socket.bind("tcp://*:5555")

group_alive_socket = context.socket(zmq.REQ)
import threading

user_list = {}

grouplist = {}

def handle_registration_request(socket):
    message = socket.recv()
    request = json.loads(message.decode('utf-8'))
    if "uid" in request.keys():
        print(f" GROUP LIST REQ from {request['uid']} at IP {request['ip']}")
        user_list[request['uid']] = request['ip']
        socket.send_string(f'{{"group_list": {json.dumps(grouplist)}}}')

    elif "gid" in request.keys():
        print(f"Received registration request for group {request['gid']} at IP {request['ip']}")
        grouplist[request['gid']] = request['ip']
        socket.send_string("GROUP REG SUCCESS")
    return 0
def check_group_alive():
    if len(grouplist)==0:
        print("No groups to check")
    for group in list(grouplist.keys()):
        group_alive_socket.connect(f"tcp://{grouplist[group]}")
        message = f'{{"message": "ALIVE?","action": "check" }}'
        group_alive_socket.send_string(message)
        response = group_alive_socket.recv()
        print(f"Received response: {response.decode('utf-8')}")
        if response.decode('utf-8') == "ALIVE":
            print(f"Group {group} is alive")
        else:
            print(f"Group {group} is dead")
            del grouplist[group]
        group_alive_socket.disconnect(f"tcp://{grouplist[group]}")
    return 0
#  Do some 'work'
seconds=0
while True:
    #  Wait for next request from client
    handle_registration_request(registration_req_socket)
    #  Do some 'work'
    # time.sleep(0.25)
