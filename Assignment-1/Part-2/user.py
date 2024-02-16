

# message server - port = 5555
# group server port - to be recieved

import uuid
import zmq
import random
import json
context = zmq.Context()
# get random port number
client_port = random.randint(7000, 9999)

ip_address = "localhost:"+str(client_port)

# get random user id
user_id = str(uuid.uuid1())

#  Socket to talk to server
message_server_socket = context.socket(zmq.REQ)
# message_server_socket.connect("tcp://34.143.209.14:5555")
message_server_socket.connect("tcp://localhost:5555")

group_server_socket = context.socket(zmq.REQ)
online_groups = {}


def GetGroupList():
    message = f'{{"uid": "{user_id}", "ip": "{ip_address}"}}'
    message_server_socket.send_string(message)
    group_list = message_server_socket.recv()
    # parse the group list
    group_list = json.loads(group_list.decode('utf-8'))['group_list']
    currently_online_groups = {}
    for key, value in group_list.items():
        currently_online_groups[key] = value
        print(f"Group {key} is online at {value}")
    
    return currently_online_groups        
def sendJoinRequest():
    group_id = input("Enter the group id you want to join: ")
    message = f'{{"uid": "{user_id}","action":"join"}}'
    group_server_socket.connect(f"tcp://{online_groups[group_id]}")
    group_server_socket.send_string(message)
    response = group_server_socket.recv()
    print(f"Received response: {response.decode('utf-8')}")
    group_server_socket.disconnect(f"tcp://{online_groups[group_id]}")

def sendLeaveRequest():

    group_id = input("Enter the group id you want to leave: ")
    message = f'{{"uid": "{user_id}", "action":"leave"}}'
    group_server_socket.connect(f"tcp://{online_groups[group_id]}")
    group_server_socket.send_string(message)
    response = group_server_socket.recv()
    print(f"Received response: {response.decode('utf-8')}")
    group_server_socket.disconnect(f"tcp://{online_groups[group_id]}")


def GetMessages():
    group_id = input("Enter the group id you want to see messages for: ")
    timestamp = input("Enter the timestamp from which you want to see messages in HH:MM:SS format(optional): ")
    if timestamp:
        message = f'{{"uid": "{user_id}", "timestamp": "{timestamp}", "action":"get_messages"}}'
    else:
        message = f'{{"uid": "{user_id}", "action":"get_messages"}}'
    group_server_socket.connect(f"tcp://{online_groups[group_id]}")
    group_server_socket.send_string(message)
    response = group_server_socket.recv()
    print(f"Received response: {response.decode('utf-8')}")
    group_server_socket.disconnect(f"tcp://{online_groups[group_id]}") 

def SendMessage():
    group_id = input("Enter the group id you want to send message to: ")
    message = input("Enter the message: ")
    message = f'{{"uid": "{user_id}", "message": "{message}", "action":"send_message"}}'
    group_server_socket.connect(f"tcp://{online_groups[group_id]}")
    group_server_socket.send_string(message)
    response = group_server_socket.recv()
    print(f"Received response: {response.decode('utf-8')}")
    group_server_socket.disconnect(f"tcp://{online_groups[group_id]}")

online_groups=GetGroupList()
while True:
    print("1. Join a group")
    print("2. Leave a group")
    print("3. Get messages from a group")
    print("4. Send message to a group")
    print("5. Get Group List again")
    print("6. Exit")

    choice = int(input("Enter your choice: "))
    if choice == 1:
        sendJoinRequest()
    elif choice == 2:
        sendLeaveRequest()
    elif choice == 3:
        GetMessages()
    elif choice == 4:
        SendMessage()
    elif choice == 5:
        online_groups=GetGroupList()
    elif choice == 6:
        break
    else:
        print("Invalid choice")
        continue