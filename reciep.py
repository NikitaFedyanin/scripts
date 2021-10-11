import pika


connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))

# Подключение к AMQP
channel = connection.channel()


def callback(ch, method, properties, body):
    print(" [x] Received %r" % (body,))


channel.queue_declare(queue='hello')

channel.basic_consume(callback,
                      queue='hello',
                      no_ack=True)

channel.start_consuming()