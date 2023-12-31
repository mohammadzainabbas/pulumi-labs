#!/bin/bash

home_dir="/home/ubuntu"
output_file="$home_dir/output.log"

AMI_ID=$(curl http://169.254.169.254/latest/meta-data/ami-id)
INSTANCE_ID=$(curl http://169.254.169.254/latest/meta-data/instance-id)
HOSTNAME=$(curl http://169.254.169.254/latest/meta-data/public-hostname)
REGION=$(curl http://169.254.169.254/latest/meta-data/placement/region)

WEB_PAGE="""
<!doctype html>
<html>
<head>
  <meta charset='utf-8'>
  <title>Super-amazing static website!</title>
  <meta name='viewport' content='width=device-width, initial-scale=1, shrink-to-fit=no'>

  <style>
      body {
        background-color: lightblue;
      }
  </style>
</head>

<body>
<h1>Deployed via Pulumi</h1>
<p>Instance ID: $INSTANCE_ID</p>
<p>Public Hostname: $HOSTNAME</p>
<p>Region: $REGION</p>
<p>AMI ID: $AMI_ID</p>
<p>Made with ♥ using <a href='https://pulumi.com'>Pulumi</a>.</p>
</body>
</html>
"""

sudo apt update -y && sudo apt install -y apache2 python3 && sudo systemctl start apache2 && sudo systemctl enable apache2 && echo "$WEB_PAGE" | sudo tee /var/www/html/index.html $output_file

AWS_REGION='<AWS Region>'  # replace with your region
ALLOCATION_ID='<Elastic IP Allocation-ID>'  # replace with your allocation id

# shellcheck disable=SC2155
export TOKEN=$(curl -s -X PUT "http://169.254.169.254/latest/api/token" -H "X-aws-ec2-metadata-token-ttl-seconds: 600")
curl -s -H "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/hostname | sudo tee -a $output_file
curl -s -H "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/placement/region | sudo tee -a $output_file
python3 -m pip install awscli | sudo tee -a $output_file
aws --version | sudo tee -a $output_file
aws --region "$AWS_REGION" ec2 associate-address --instance-id "$INSTANCE_ID" --allocation-id "$ALLOCATION_ID" &>> $output_file  # replace <YourRegion> with your region
