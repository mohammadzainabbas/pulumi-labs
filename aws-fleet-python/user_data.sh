#!/bin/bash
echo "Hello, World from Pulumi!" > index.html
nohup python3 -m http.server 80 &

aws --region eu-west-3 ec2 allocate-address --domain vpc --query 'AllocationId' --output text