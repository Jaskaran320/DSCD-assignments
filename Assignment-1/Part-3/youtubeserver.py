import pika
import sys
import json


print("Server started")

connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()

channel.queue_declare(queue="login_queue", durable=True)

users={}
# youtubers={"ABC":["nsr"],"DEF":["nsr","nsr1"],"XYZ":["nsr","nsr1","nsr2"]}
youtubers={}
sent_videos = {}

channel.queue_declare(queue="youtuber_queue", durable=True)
# sent videos for every youtuber
for user in users.keys():
    youtubers = users[user]
    sent_videos[user]=[]
    for youtuber in youtubers:
        sent_videos[user].append({youtuber:youtubers[youtuber]})
    # channel.queue_declare(queue=youtuber, durable=True)
print(sent_videos)
# declare a exchange for every youtuber
for youtuber in youtubers.keys():
    channel.exchange_declare(exchange=youtuber, exchange_type="fanout")


def logger():
    # write state of users and youtubers with timestamps to a file
    with open("log.txt", "a") as file:
        file.write(f"{users} {youtubers} \n")
    


# call back function that handles messages on a queue called login_queue
def handle_login(ch, method, properties, body):
    # parse the message
    message = body.decode()
    print(message)

    # convert the message to a dictionary
    message_dict = json.loads(message)
    print(type(message_dict))

    if len(message_dict.keys())==1:
        # simple login 
        user = message_dict["user"]
        if user in users:
            print("User already exists")
            # do nothing special if the user already exists
        else:
            # if new user create the dedicated queue for the user
            channel.queue_declare(queue=user, durable=True)
            users[user]=[]
            print("User created")
            
    if len(message_dict.keys())==3:
        # subscribe or unsubscribe a user to a youtuber
        user = message_dict["user"]
        youtuber = message_dict["youtuber"]
        subscribe = message_dict["subscribe"]

        if subscribe:
            if youtuber in youtubers:
                if user in users:
                    if youtuber not in users[user]:
                        users[user].append(youtuber)
                        print("Subscribed")
                        channel.queue_bind(exchange=youtuber, queue=user)
                        publish_video_first_time(user,youtuber)
                    else:
                        print("Already Subscribed")
                else:
                    users[user]=[]
                    channel.queue_declare(queue=user, durable=True)
                    print("User created")
                    users[user].append(youtuber)
                    print("Subscribed")
                    channel.queue_bind(exchange=youtuber, queue=user)
                    publish_video_first_time(user,youtuber)
            else:
                print("Youtuber does not exist")
        else:
            if user in users:
                if youtuber in users[user]:
                    users[user].remove(youtuber)
                    print("Unsubscribed")
                    channel.queue_unbind(exchange=youtuber, queue=user)
                else:
                    print("Not Subscribed")
            else:
                print("User does not exist")
# declare a queue called login_queue

def handle_youtuber(ch, method, properties, body):
    # parse the message
    message = body.decode()
    print(message)
    message_dict = json.loads(message)
    youtuber = message_dict["youtuber"]
    video = message_dict["video"]
    if youtuber in youtubers:
        youtubers[youtuber].append(video)
        print("Video added")
        # publish the video to the dedicated queue for the youtuber
        for user in users.keys():
            if youtuber in users[user]:
                message = f'{{"youtuber": "{youtuber}", "video": "{video}"}}'
                channel.basic_publish(exchange=youtuber, routing_key="", body=message)
                print(f"Video published to {user}")
    else:
        # add the youtuber to the list of youtubers
        youtubers[youtuber]=[video]
        print("Youtuber added")
        print("Video added")

        for user in users.keys():
            if youtuber in users[user]:
                message = f'{{"youtuber": "{youtuber}", "video": "{video}"}}'
                channel.basic_publish(exchange=youtuber, routing_key="", body=message)
                print(f"Video published to {user}")

def publish_video_first_time(user, youtuber):
    # publish the videos that the youtuber has already published
    for video in youtubers[youtuber]:
        message = f'{{"youtuber": "{youtuber}", "video": "{video}"}}'
        channel.basic_publish(exchange="", routing_key=user, body=message)
        print(f"Video published to {user}")



# publish_videos()

# consume messages from the login_queue

channel.basic_consume(queue="login_queue", auto_ack=True, on_message_callback=handle_login)
channel.basic_consume(queue='youtuber_queue', on_message_callback=handle_youtuber, auto_ack=True)
channel.start_consuming()

