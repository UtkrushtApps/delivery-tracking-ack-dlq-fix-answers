#!/usr/bin/env python3
"""Publishes a small batch of sample delivery updates.

Reads payloads from sample_messages.json and publishes each one to the
tracking exchange with routing key 'delivery.update'.
"""

import json

import pika

AMQP_HOST = "127.0.0.1"
AMQP_PORT = 5672
AMQP_VHOST = "logistics"
AMQP_USER = "logistics_app"
AMQP_PASS = "logistics_pass"

EXCHANGE = "tracking.exchange"
ROUTING_KEY = "delivery.update"


def publish_batch():
    with open("sample_messages.json", "r") as fh:
        messages = json.load(fh)

    credentials = pika.PlainCredentials(AMQP_USER, AMQP_PASS)
    params = pika.ConnectionParameters(
        host=AMQP_HOST,
        port=AMQP_PORT,
        virtual_host=AMQP_VHOST,
        credentials=credentials,
    )
    connection = pika.BlockingConnection(params)
    channel = connection.channel()

    for msg in messages:
        channel.basic_publish(
            exchange=EXCHANGE,
            routing_key=ROUTING_KEY,
            body=json.dumps(msg),
            properties=pika.BasicProperties(
                content_type="application/json",
                delivery_mode=2,
            ),
        )
        print(f"published: tracking_id={msg.get('tracking_id')} "
              f"status={msg.get('status')}")

    connection.close()
    print("Batch published.")


if __name__ == "__main__":
    publish_batch()
