import pika
import json
import base64 as bs64
from supportive_methods import extract_text_from_bytes
import configparser

config = configparser.ConfigParser()
config.read('config.ini')

rabbit_user = config['BROKER']['RABBITMQ_USER']
rabbit_password = config['BROKER']['RABBIT_PASSWORD']
rabbit_host = config['BROKER']['RABBIT_HOST']
rabbit_port = config['BROKER']['RABBIT_PORT']
rabbit_vhost = config['BROKER']['VIRTUAL_HOST']

credentials = pika.PlainCredentials(rabbit_user, rabbit_password)
connection = pika.BlockingConnection(pika.ConnectionParameters(host=rabbit_host,
                                                               port=rabbit_port,
                                                               virtual_host=rabbit_vhost,
                                                               credentials=credentials))


def callback(ch, method, properties, body):

    print(' [*] Message recieved. Start processing')
    input = json.loads(body)
    string_binary_bs64_pdf = input['request']['fileContent']  # Extracting decoded binary
    binary_bs64_pdf = string_binary_bs64_pdf.encode()  # Converting binary to string
    pdf = bs64.b64decode(binary_bs64_pdf)  # Decoding bs64 str into origin bytes


    print(" [*] Starting OCR")
    try:
        ocr_result = extract_text_from_bytes(pdf)
        print("[*] OCR complete")

        # updating output
        request = input["request"]
        request["ocrResult"] = ocr_result
        request["errorMessage"] = "noErrorMessage"

        output = {
            "metadata": input["metadata"],
            "response": request
        }



    except Exception as e:

        print(f'Ups! Some error occur {e}')

        # updating output
        request = input["request"]
        request["ocrResult"] = []
        request["errorMessage"] = e

        output = {
            "metadata": input["metadata"],
            "response": request
        }

    channel_out = connection.channel()

    out_queue_name = config['CONSUMER']['OUTPUT_QUEUE_NAME']
    out_exchange_name = config['CONSUMER']['OUTPUT_EXCHANGE_NAME']

    channel_out.queue_bind(
        exchange=out_exchange_name,
        queue=out_queue_name
    )

    print("[*] Sending respond")

    channel_out.basic_publish(exchange=out_exchange_name,
                              routing_key=out_queue_name,
                              body=json.dumps(output))
    print("[*] Respond sent")
    channel_out.close()


def main():
    channel = connection.channel()

    input_queue_name = config['PRODUCER']['INPUT_QUEUE_NAME']
    input_exchange_name = config['PRODUCER']['INPUT_EXCHANGE_NAME']

    channel.queue_bind(
        exchange=input_queue_name,
        queue=input_exchange_name
    )

    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue=input_queue_name,
                          auto_ack=True,
                          on_message_callback=callback)

    print(' [*] Waiting for messages. To exit press CTRL+C')
    channel.start_consuming()

if __name__ == '__main__':
    main()