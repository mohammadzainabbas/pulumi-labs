#!/bin/bash

home_dir="/home/ubuntu"
output_file="$home_dir/output.log"

AMI_ID=$(curl http://169.254.169.254/latest/meta-data/ami-id)
INSTANCE_ID=$(curl http://169.254.169.254/latest/meta-data/instance-id)
HOSTNAME=$(curl http://169.254.169.254/latest/meta-data/hostname)
AWS_REGION=$(curl http://169.254.169.254/latest/meta-data/placement/region)
INSTANCE_TYPE=$(curl http://169.254.169.254/latest/meta-data/instance-type)
PUBLIC_IP=$(curl http://169.254.169.254/latest/meta-data/public-ipv4)
ACCOUNT_ID=$(curl http://169.254.169.254/latest/meta-data/identity-credentials/ec2/info | jq .AccountId)

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
<p>Instance Type: $INSTANCE_TYPE</p>
<p>Instance ID: $INSTANCE_ID</p>
<p>Hostname: $HOSTNAME</p>
<p>Region: $AWS_REGION</p>
<p>AMI ID: $AMI_ID</p>
<p>Made with ♥ using <a href='https://pulumi.com'>Pulumi</a>.</p>
</body>
</html>
"""

setup_instance() {
    sudo apt update -y && \
    sudo apt install -y apache2 && \
    sudo systemctl start apache2 && \
    sudo systemctl enable apache2 && \
    echo "$WEB_PAGE" | sudo tee /var/www/html/index.html $output_file
}

# ------------------------------
# Notify via ntfy.sh
# ------------------------------
topic="mohammadzainabbas"

success_notify() {
    curl ntfy.sh \
    -d '{
        "topic": "$topic",
        "message": "Disk space is low at 5.1 GB",
        "title": "Low disk space alert",
        "tags": ["warning","cd"],
        "priority": 4,
        "attach": "https://filesrv.lan/space.jpg",
        "filename": "diskspace.jpg",
        "click": "https://homecamera.lan/xasds1h2xsSsa/",
        "actions": [{ "action": "view", "label": "Admin panel", "url": "https://filesrv.lan/admin" }]
    }'
}

failure_notify() {
curl ntfy.sh \
  -d '{
    "topic": "mohammadzainabbas",
    "message": "Disk space is low at 5.1 GB",
    "title": "Low disk space alert",
    "tags": ["warning","cd"],
    "priority": 4,
    "attach": "https://filesrv.lan/space.jpg",
    "filename": "diskspace.jpg",
    "click": "https://homecamera.lan/xasds1h2xsSsa/",
    "actions": [{ "action": "view", "label": "Admin panel", "url": "https://filesrv.lan/admin" }]
  }'
}

main() {
    if setup_instance; then
        success_notify
    else
        failure_notify
    fi
}

main
