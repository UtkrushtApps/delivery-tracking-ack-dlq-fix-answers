#!/usr/bin/env python3
"""Delivery-tracking worker.

Consumes delivery status updates from the tracking queue and persists
each one via save_event(). save_event() simulates a flaky downstream
write that fails for 'failed-attempt' updates.
"""

import json

import pika

AMQP_HOST = "127.0.0.1"
AMQP_PORT = 5672
AMQP_VHOST = "logistics"
AMQP_USER = "logistics_app"
AMQP_PASS = "logistics_pass"

UPDATES_QUEUE = "tracking.delivery.updates"
PREFETCH_COUNT = 1


def save_event(event):
    """Simulate persisting a delivery event to the data store.

    Fails (raises) for 'failed-attempt' updates to mimic a flaky write.
    """
    if event.get("status") == "failed-attempt":
        raise RuntimeError("database timeout")
    print(f"  saved event: tracking_id={event.get('tracking_id')} "
          f"status={event.get('status')}")


def consume_delivery_updates():
    credentials = pika.PlainCredentials(AMQP_USER, AMQP_PASS)
    params = pika.ConnectionParameters(
        host=AMQP_HOST,
        port=AMQP_PORT,
        virtual_host=AMQP_VHOST,
        credentials=credentials,
    )
    connection = pika.BlockingConnection(params)
    channel = connection.channel()

    # Do not let the broker send an unlimited number of unacknowledged
    # deliveries to this worker. With manual acknowledgements, this keeps
    # processing bounded and ensures a message remains in the queue until the
    # worker explicitly acknowledges it after save_event() succeeds.
    channel.basic_qos(prefetch_count=PREFETCH_COUNT)

    def on_message(ch, method, properties, body):
        try:
            event = json.loads(body)
            print(f"received update: tracking_id={event.get('tracking_id')} "
                  f"status={event.get('status')}")
            save_event(event)
        except Exception as exc:
            # Persistence failed. Reject once without requeue so RabbitMQ routes
            # the message through the queue's DLX instead of redelivering it in
            # an endless loop on tracking.delivery.updates.
            print(f"  failed to save update; rejecting without requeue: {exc}")
            ch.basic_reject(
                delivery_tag=method.delivery_tag,
                requeue=False,
            )
            return

        # Only acknowledge after save_event() completed successfully. At this
        # point RabbitMQ can safely remove the message from the main queue.
        ch.basic_ack(delivery_tag=method.delivery_tag)

    channel.basic_consume(
        queue=UPDATES_QUEUE,
        on_message_callback=on_message,
        auto_ack=False,
    )

    print("Worker started. Waiting for delivery updates. Press CTRL+C to exit.")
    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        print("Stopping worker...")
        channel.stop_consuming()
    finally:
        connection.close()


if __name__ == "__main__":
    consume_delivery_updates()
