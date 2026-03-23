#!/bin/sh
set -e

awslocal sqs create-queue --queue-name reports-jobs-dlq >/dev/null

DLQ_ARN="$(awslocal sqs get-queue-attributes \
  --queue-url http://localhost:4566/000000000000/reports-jobs-dlq \
  --attribute-names QueueArn \
  --query 'Attributes.QueueArn' \
  --output text)"

awslocal sqs create-queue \
  --queue-name reports-jobs-standard \
  --attributes "{\"VisibilityTimeout\":\"90\",\"ReceiveMessageWaitTimeSeconds\":\"20\",\"RedrivePolicy\":\"{\\\"deadLetterTargetArn\\\":\\\"${DLQ_ARN}\\\",\\\"maxReceiveCount\\\":\\\"3\\\"}\"}" \
  >/dev/null

awslocal sqs create-queue \
  --queue-name reports-jobs-high \
  --attributes "{\"VisibilityTimeout\":\"90\",\"ReceiveMessageWaitTimeSeconds\":\"20\",\"RedrivePolicy\":\"{\\\"deadLetterTargetArn\\\":\\\"${DLQ_ARN}\\\",\\\"maxReceiveCount\\\":\\\"3\\\"}\"}" \
  >/dev/null

awslocal s3 mb s3://reports-results >/dev/null 2>&1 || true
