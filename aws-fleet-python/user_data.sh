#!/bin/bash

home_dir="/home/ubuntu"
output_file="$home_dir/output.log"

sudo apt update -y && sudo apt install -y apache2 python3 && sudo systemctl start apache2 && sudo systemctl enable apache2 && echo '<h1>Deployed via Pulumi</h1>' | sudo tee /var/www/html/index.html $output_file

INSTANCE_ID=$(curl http://169.254.169.254/latest/meta-data/instance-id)
AWS_REGION='<AWS Region>'  # replace with your region
ALLOCATION_ID='<Elastic IP Allocation-ID>'  # replace with your allocation id

# shellcheck disable=SC2155
export TOKEN=$(curl -s -X PUT "http://169.254.169.254/latest/api/token" -H "X-aws-ec2-metadata-token-ttl-seconds: 600")
curl -s -H "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/hostname
curl -s -H "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/placement/region
python3 -m pip install awscli
aws --version | sudo tee -a $output_file
aws --region "$AWS_REGION" ec2 associate-address --instance-id "$INSTANCE_ID" --allocation-id "$ALLOCATION_ID" &>> $output_file  # replace <YourRegion> with your region
