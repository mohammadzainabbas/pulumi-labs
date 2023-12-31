#!/bin/bash

output_file="$HOME/Desktop/index.html"

AMI_ID="AWS AMI_ID"
INSTANCE_ID="AWS INSTANCE_ID"
HOSTNAME="AWS HOSTNAME"
REGION="AWS REGION"

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
    echo "$WEB_PAGE" | tee "$output_file"
}

# ------------------------------
# Notify via ntfy.sh
# ------------------------------
topic="mohammadzainabbas"

success_notify() {
    curl ntfy.sh \
    -d "{
        \"topic\": \"$topic\",
        \"message\": \"Disk space is low at 5.1 GB\",
        \"title\": \"Success: Low disk space alert\",
        \"tags\": [\"warning\",\"cd\"],
        \"priority\": 4,
        \"attach\": \"https://filesrv.lan/space.jpg\",
        \"filename\": \"diskspace.jpg\",
        \"click\": \"https://homecamera.lan/xasds1h2xsSsa/\",
        \"actions\": [{ \"action\": \"view\", \"label\": \"Admin panel\", \"url\": \"https://filesrv.lan/admin\" }]
    }"
}

failure_notify() {
curl ntfy.sh \
  -d '{
    "topic": "mohammadzainabbas",
    "message": "Disk space is low at 5.1 GB",
    "title": "Failed: Low disk space alert",
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
