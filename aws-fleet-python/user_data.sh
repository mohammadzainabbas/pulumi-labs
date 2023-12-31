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

setup_instance() {
  sudo apt update -y && sudo apt install -y apache2 && sudo systemctl start apache2 && sudo systemctl enable apache2 && echo "$WEB_PAGE" | sudo tee /var/www/html/index.html $output_file
}

(sudo apt update -y && sudo apt install -y apache2 && sudo systemctl start apache2 && sudo systemctl enable apache2 && echo "$WEB_PAGE" | sudo tee /var/www/html/index.html $output_file) && (curl \
  -H "Title: Docker build has finished successfully \
  -H "Priority: urgent" \
  -H "Tags: tada,spark" \
  -d "Successfully build docker image. Let's start with the new docker image!." \
  ntfy.sh/mohammadzainabbas) || (curl \
  -H "Title: Docker build failed" \
  -H "Priority: urgent" \
  -H "Tags: warning,skull" \
  -d "Failed to build docker image. Have a look!." \
  ntfy.sh/mohammadzainabbas)