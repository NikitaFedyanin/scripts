import pika



def send_message(mess):
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))

    # Подключение к AMQP
    channel = connection.channel()

    channel.queue_declare(queue='hello')

    channel.basic_publish(exchange='',
                          routing_key='hello',
                          body=mess)


pass