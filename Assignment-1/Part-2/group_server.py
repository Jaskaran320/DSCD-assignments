# message server - port = 5555
# group server port - to be sent

import zmq
import random
import json
import time
from datetime import datetime
import threading

context = zmq.Context()
# get random port number
client_port = 6010

ip_address = "localhost:"+str(client_port)

# get random group id
group_id = random.randint(1000, 9999)

#  Socket to talk to server
message_server_socket = context.socket(zmq.REQ)
message_server_socket.connect("tcp://34.143.209.14:5555")

group_server_socket = context.socket(zmq.ROUTER)
group_server_socket.bind("tcp://*:"+str(client_port))


message_lock = threading.Lock()

user_list = []
messages = [
    {"uid": 1000, "message": "Hello World", "timestamp": "12:00:00"},
    {"uid": 1001, "message": "Hello Universe", "timestamp": "12:01:00"},
    {"uid": 1002, "message": "Hello Galaxy", "timestamp": "12:02:00"},
    {"uid": 1003, "message": "Hello Star", "timestamp": "12:03:00"},
    {"uid": 1004, "message": "Hello Planet", "timestamp": "12:04:00"},
    {"uid": 1005, "message": "Hello Moon", "timestamp": "12:05:00"},
]


def RegisterGroup():
    message = f'{{"gid": "{group_id}", "ip": "{ip_address}"}}'
    message_server_socket.send_string(message)
    response = message_server_socket.recv()
    print(f"Received response: {response.decode('utf-8')}")

def handleJoinRequest(socket,message,address):
    print("seghshsh",message)
    request = json.loads(message)
    print(f"Received join request from user {request['uid']}")
    socket.send_multipart([address,b'',b"SUCCESS"])
    if request['uid'] not in user_list:
        user_list.append(request['uid'])
    print(user_list)
    return 0

def handleLeaveRequest(socket,message,address):

    request = json.loads(message)
    print(f"Received leave request from user {request['uid']}")
    socket.send_multipart([address,b'',b"SUCCESS"])
    user_list.remove(request['uid'])
    # print(user_list)
    return 0

def handleGetMessagesRequest(socket,message,address):
    with message_lock:
        request = json.loads(message)
        
        if request['uid'] not in user_list:
            print(f"User {request['uid']} is not a part of the group")
            socket.send_multipart([address,b'',b"FAILURE"])
        else:
            print(f"Received get messages request from user {request['uid']}")
            response = []
            if "timestamp" in request.keys():
                for msg in messages:
                    if msg['timestamp'] >= request['timestamp']:
                        response.append(msg)
            else:
                for msg in messages:
                    response.append(msg)
            socket.send_multipart([address,b'',json.dumps(response).encode('utf-8')])

# socket.send_string(json.dumps(response))
    return 0

def handleSendMessageRequest(socket,message,address):
    with message_lock:
        request = json.loads(message)
        if request['uid'] not in user_list:
            print(f"User {request['uid']} is not a part of the group")
            socket.send_multipart([address,b'',b"FAILURE"])
    # return 0
        else:
            print(f"Received send message request from user {request['uid']}")
            text = request['message']

            #  get the current time in HH:MM:SS format

            current_time = datetime.now().strftime('%H:%M:%S')

            messages.append({"uid": request['uid'], "message": text, "timestamp": str(current_time)})
            socket.send_multipart([address,b'',b"SUCCESS"])
    return 0


RegisterGroup()
while True:
    #  Wait for next request from client

    message = group_server_socket.recv_multipart()
    # print(f"Received request: {message}")
    address = message[0]
    message = message[2].decode('utf-8')
        # print(f"Part {i}: {part.decode('utf-8')}")

    request = json.loads(message)
    if request['action'] == "join":
        threading.Thread(target=handleJoinRequest,args=(group_server_socket,message,address)).start()
        # handleJoinRequest(group_server_socket,message)
    if request['action'] == "leave":
        threading.Thread(target=handleLeaveRequest,args=(group_server_socket,message,address)).start()
        # handleLeaveRequest(group_server_socket,message)
    if request['action'] == "get_messages":
        threading.Thread(target=handleGetMessagesRequest,args=(group_server_socket,message,address)).start()
        # handleGetMessagesRequest(group_server_socket,message)
    if request['action'] == "send_message":
        threading.Thread(target=handleSendMessageRequest,args=(group_server_socket,message,address)).start()
        
        # handleSendMessageRequest(group_server_socket,message)

