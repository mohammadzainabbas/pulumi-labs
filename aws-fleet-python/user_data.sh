#!/bin/bash
set -ex

INSTANCE_ID=$(curl http://169.254.169.254/latest/meta-data/instance-id)
ALLOCATION_ID=$2  # replace <YourRegion> with your region
aws --region $1 ec2 associate-address --instance-id $INSTANCE_ID --allocation-id $ALLOCATION_ID   # replace <YourRegion> with your region

echo "Hello, World from Pulumi!" > index.html
nohup python3 -m http.server 80 &
