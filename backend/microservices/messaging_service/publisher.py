# publisher.py — REMOVED
# RabbitMQ publishing for message.sent events has been moved to the
# Negotiate composite service, which publishes directly after storing
# the message. The messaging service is now a pure atomic service
# with no AMQP dependency.
