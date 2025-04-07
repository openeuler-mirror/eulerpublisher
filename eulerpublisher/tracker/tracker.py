import pika
import json
from multiprocessing import Process

class Tracker(Process):
    def __init__(self, logger, config, db):
        super().__init__()
        self.logger = logger
        self.config = config
        self.db = db
        self.logger.info("Tracker initialized")

    def run(self):
        conn = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
        channel = conn.channel()

        channel.exchange_declare(exchange='eulerpublisher', exchange_type='topic')

        queue = channel.queue_declare(queue='', exclusive=True)
        queue_name = queue.method.queue

        channel.queue_bind(exchange='eulerpublisher', queue=queue_name, routing_key='tracker')

        def callback(ch, method, properties, body):
            response = json.loads(body)
            self.logger.info(f"Received response: {response}")
            
        channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)
        channel.start_consuming()