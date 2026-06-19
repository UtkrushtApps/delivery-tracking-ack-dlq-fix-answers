# Solution Steps

1. In definitions.json, keep the normal direct exchange tracking.exchange and durable main queue tracking.delivery.updates, but add queue arguments x-dead-letter-exchange set to tracking.dlx and x-dead-letter-routing-key set to delivery.update.

2. Ensure tracking.dlx is declared as a durable direct exchange, tracking.delivery.dlq is declared as a durable queue, and tracking.dlx is bound to tracking.delivery.dlq with routing key delivery.update.

3. In consumer.py, disable lossy auto acknowledgements by changing basic_consume from auto_ack=True to auto_ack=False.

4. Before consuming, call channel.basic_qos(prefetch_count=1) so RabbitMQ sends only one unacknowledged message at a time to this worker.

5. Wrap message decoding and save_event(event) in a try/except block inside the consumer callback.

6. On success, call ch.basic_ack(delivery_tag=method.delivery_tag) only after save_event(event) returns successfully; this is the point where RabbitMQ may remove the message from tracking.delivery.updates.

7. On any save_event failure, especially the simulated status failed-attempt failure, call ch.basic_reject(delivery_tag=method.delivery_tag, requeue=False) and return without acknowledging. Because the main queue has DLX arguments, RabbitMQ dead-letters that rejected message to tracking.dlx and then into tracking.delivery.dlq.

8. Publish messages with producer.py as persistent messages using delivery_mode=2, which preserves queued messages on durable queues across broker restarts.

9. To verify manually, start RabbitMQ with docker compose up -d, run python3 producer.py, run python3 consumer.py until the batch is processed, and stop the consumer after the successful messages are saved and the failed-attempt message is rejected.

10. Confirm the main queue has drained and the DLQ contains exactly one message, then restart the broker and confirm the DLQ message remains because both the queue and published messages are durable.

