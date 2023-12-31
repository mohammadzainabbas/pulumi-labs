#!/bin/bash

output_file="$HOME/Desktop/output.log"

AMI_ID="AWS AMI_ID"
INSTANCE_ID="AWS INSTANCE_ID"
HOSTNAME="AWS HOSTNAME"
AWS_REGION="AWS AWS_REGION"
INSTANCE_TYPE="AWS INSTANCE_TYPE"
PUBLIC_IP="AWS PUBLIC_IP"
ACCOUNT_ID="AWS ACCOUNT_ID"

setup_instance() {
    local WEB_PAGE="""
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
    echo "$WEB_PAGE" | tee /var/www/html/index.html "$output_file"
}

# ------------------------------
# Notify via ntfy.sh
# ------------------------------
topic="mohammadzainabbas"
github="https://github.com/mohammadzainabbas/pulumi-labs"
project="aws-fleet-python"
_project_link="$github/tree/main/$project"
_click="$_project_link"
_attach="https://get.pulumi.com/new/button.svg"
_filename="pulumi.svg"
_pulumi="https://app.pulumi.com/mohammadzainabbas/projects"

start_notify() {
	_title="Deploying '$INSTANCE_TYPE' with '$PUBLIC_IP' IPv4 🦋"
	_msg="Started setup scripts on Instance ID: '$INSTANCE_ID' with AMI: '$AMI_ID' at '$AWS_REGION' by account: '$ACCOUNT_ID' 🚧"

    curl ntfy.sh \
    -d "{
        \"topic\": \"$topic\",
        \"message\": \"$_msg\",
        \"title\": \"$_title\",
        \"tags\": [\"package\"],
        \"priority\": 4,
        \"click\": \"$_click\",
        \"actions\": [
				{ \"action\": \"view\", \"label\": \"Open GitHub\", \"url\": \"$_project_link\", \"clear\": false }, 
				{ \"action\": \"view\", \"label\": \"View Pulumi\", \"url\": \"$_pulumi\", \"clear\": false }
			]
    }"
}

end_notify() {
    local TIME=$1
	_title="Took $TIME secs to run setup scripts on '$INSTANCE_TYPE' with '$PUBLIC_IP' IPv4 🌟"
	_msg="Setup scripts completed on Instance ID: '$INSTANCE_ID' with AMI: '$AMI_ID' at '$AWS_REGION' by account: '$ACCOUNT_ID' 👨‍💻"

    curl ntfy.sh \
    -d "{
        \"topic\": \"$topic\",
        \"message\": \"$_msg\",
        \"title\": \"$_title\",
        \"tags\": [\"alarm_clock\"],
        \"priority\": 4,
        \"click\": \"$_click\",
        \"actions\": [
				{ \"action\": \"view\", \"label\": \"Open GitHub\", \"url\": \"$_project_link\", \"clear\": false }, 
				{ \"action\": \"view\", \"label\": \"View Pulumi\", \"url\": \"$_pulumi\", \"clear\": false }
			]
    }"
}

success_notify() {
	_title="Setup deployed on '$INSTANCE_TYPE' with '$PUBLIC_IP' IPv4 🚀"
	_msg="Instance ID: '$INSTANCE_ID' was deployed with AMI: '$AMI_ID' at '$AWS_REGION' by account: '$ACCOUNT_ID' 🚀"
    _web_url="http://$PUBLIC_IP"

    curl ntfy.sh \
    -d "{
        \"topic\": \"$topic\",
        \"message\": \"$_msg\",
        \"title\": \"$_title\",
        \"tags\": [\"white_check_mark\",\"tada\"],
        \"priority\": 4,
        \"attach\": \"$_attach\",
        \"filename\": \"$_filename\",
        \"click\": \"$_click\",
        \"actions\": [
				{ \"action\": \"view\", \"label\": \"Open GitHub\", \"url\": \"$_project_link\", \"clear\": false }, 
				{ \"action\": \"view\", \"label\": \"View Pulumi\", \"url\": \"$_pulumi\", \"clear\": false },
				{ \"action\": \"view\", \"label\": \"View Website\", \"url\": \"$_web_url\", \"clear\": false }
			]
    }"
}

failure_notify() {
	_title="Unable to deploy setup on '$INSTANCE_TYPE' with '$PUBLIC_IP' IPv4 💔"
	_msg="Debug Info - Instance ID: '$INSTANCE_ID' with AMI: '$AMI_ID' at '$AWS_REGION' by account: '$ACCOUNT_ID' 💔"

    curl ntfy.sh \
    -d "{
        \"topic\": \"$topic\",
        \"message\": \"$_msg\",
        \"title\": \"$_title\",
        \"tags\": [\"x\",\"face_with_head_bandage\"],
        \"priority\": 5,
        \"attach\": \"$_attach\",
        \"filename\": \"$_filename\",
        \"click\": \"$_click\",
        \"actions\": [
				{ \"action\": \"view\", \"label\": \"Open GitHub\", \"url\": \"$_project_link\", \"clear\": false }, 
				{ \"action\": \"view\", \"label\": \"View Pulumi\", \"url\": \"$_pulumi\", \"clear\": false }
			]
    }"
}

log() {
    echo "[ log ] $1" | tee -a "$output_file"
}

run() {
    local start=$(date +%s.%N);
    "$*" | tee -a "$output_file"
    local end=$(date +%s.%N);
    local time_diff=$(echo "$end - $start" | bc);
    echo "[ run ] $* took $time_diff secs" | tee -a "$output_file"
}

main() {
    start_time=$(date +%s.%N);
    run start_notify;
    log "start_notify()"
    if run setup_instance; then
        log "setup_instance()"
        run success_notify
        log "success_notify()"
    else
        run failure_notify
        log "failure_notify()"
    fi
    end_time=$(date +%s.%N);
    time_diff=$(echo "$end_time - $start_time" | bc);
    run end_notify "$time_diff";
    log "end_notify()"
}

main
