#!/bin/bash
set -ex

INSTANCE_ID=$(curl http://169.254.169.254/latest/meta-data/instance-id)
ALLOCATION_ID=$(aws --region <YourRegion> ec2 allocate-address --domain vpc --query 'AllocationId' --output text)  # replace <YourRegion> with your region
aws --region <YourRegion> ec2 associate-address --instance-id $INSTANCE_ID --allocation-id $ALLOCATION_ID   # replace <YourRegion> with your region

echo "Hello, World from Pulumi!" > index.html
nohup python3 -m http.server 80 &
