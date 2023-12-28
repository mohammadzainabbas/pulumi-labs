#!/bin/bash
set -ex

INSTANCE_ID=$(curl http://169.254.169.254/latest/meta-data/instance-id)
AWS_REGION='<AWS Region>'  # replace with your region
ALLOCATION_ID='<Allocation-ID>'  # replace with your allocation id
aws --region "$AWS_REGION" ec2 associate-address --instance-id "$INSTANCE_ID" --allocation-id "$ALLOCATION_ID"   # replace <YourRegion> with your region

echo "Hello, World from Pulumi!" > index.html
nohup python3 -m http.server 80 &
