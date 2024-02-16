import pika
import sys

# parse the command line arguments
youtuber_name = sys.argv[1]
video_name = sys.argv[2]

creds = pika.PlainCredentials('test', 'test')
connection = pika.BlockingConnection(pika.ConnectionParameters('34.0.7.140',credentials=creds))
# connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))

channel = connection.channel()

channel.queue_declare(queue='youtuber_queue',durable=True)

def publish_video(youtuber, video_name):
        # Publish video to the YouTube server as a json
        message = f'{{"youtuber": "{youtuber}", "video": "{video_name}"}}'
        channel.basic_publish(exchange='', routing_key='youtuber_queue', body=message)
        print("SUCCESS")


publish_video(youtuber_name, video_name)
connection.close()
