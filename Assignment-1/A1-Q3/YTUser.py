import pika
import sys
import time


user_name=""
action=""
youtuber=""
print(len(sys.argv))
if len (sys.argv) == 2:
    user_name = sys.argv[1]
elif len(sys.argv) == 4:
    user_name = sys.argv[1]
    action = sys.argv[3]
    youtuber = sys.argv[2]

connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()

# Declare a queue for the login 
channel.queue_declare(queue="login_queue", durable=True)
# print(" [x] Sent 'Hello World!'")
def login(user):
    # print("bssese")
    # Send login request to the YouTube Server
    message = f'{{"user": "{user}"}}'
    channel.basic_publish(exchange='', routing_key="login_queue", body=message)
    print("SUCCESS")

def update_subscription(user, youtuber, subscribe):
        # Send subscription/unsubscription request to the YouTube Server
        message = f'{{"user": "{user}", "youtuber": "{youtuber}", "subscribe": {subscribe}}}'
        channel.basic_publish(exchange='', routing_key="login_queue", body=message)
        print("SUCCESS")

def receive_notifications(ch, method, properties, body):
    # Receive and print notifications
    print("vses")
    print(f"New Notification: {body.decode()}")


if len(sys.argv) == 4:
    if action == "s":
        update_subscription(user_name, youtuber, "true")
        time.sleep(0.1)
        channel.basic_consume(queue=user_name, on_message_callback=receive_notifications, auto_ack=True)
        channel.start_consuming()
    elif action == "u":
        update_subscription(user_name, youtuber, "false")
        time.sleep(0.1)
        channel.basic_consume(queue=user_name, on_message_callback=receive_notifications, auto_ack=True)
        channel.start_consuming()
    else:
        print("Invalid action")
        sys.exit(1)
elif len(sys.argv) == 2:
    login(user_name)
    # add a delay to ensure that the user queue is created before consuming messages
    time.sleep(0.1)
    channel.basic_consume(queue=user_name, on_message_callback=receive_notifications, auto_ack=True)
    channel.start_consuming() 

