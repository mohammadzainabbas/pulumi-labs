#!/bin/bash

INSTANCE_ID=$(curl http://169.254.169.254/latest/meta-data/instance-id)
AWS_REGION='<AWS Region>'  # replace with your region
ALLOCATION_ID='<Elastic IP Allocation-ID>'  # replace with your allocation id
aws --region "$AWS_REGION" ec2 associate-address --instance-id "$INSTANCE_ID" --allocation-id "$ALLOCATION_ID"   # replace <YourRegion> with your region

echo "Hello, World from Pulumi!" > index.html
nohup python3 -m http.server 80 &

sudo yum install -y httpd && sudo systemctl start httpd && sudo systemctl enable httpd && echo '<h1>Deployed via Pulumi</h1>' | sudo tee /var/www/html/index.html