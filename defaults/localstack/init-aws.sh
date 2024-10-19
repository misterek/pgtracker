#!/bin/bash
set -e

# Wait for LocalStack to be ready
while ! aws --endpoint-url=http://localstack:4566 s3 ls; do
  sleep 1
done

# Create S3 bucket
aws --endpoint-url=http://localstack:4566 s3 mb s3://pgtracker

# Create SQS queue
aws --endpoint-url=http://localstack:4566 sqs create-queue --queue-name pgtracker-queue

# Get the SQS queue ARN
QUEUE_ARN=$(aws --endpoint-url=http://localstack:4566 sqs get-queue-attributes --queue-url http://localhost:4566/000000000000/pgtracker-queue --attribute-names QueueArn --query 'Attributes.QueueArn' --output text)

# Set up S3 event notification to SQS
aws --endpoint-url=http://localstack:4566 s3api put-bucket-notification-configuration \
    --bucket pgtracker \
    --notification-configuration '{
        "QueueConfigurations": [{
            "QueueArn": "'$QUEUE_ARN'",
            "Events": ["s3:ObjectCreated:*"]
        }]
    }'

echo "LocalStack initialization completed successfully."
