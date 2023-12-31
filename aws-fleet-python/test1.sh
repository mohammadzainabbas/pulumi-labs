#!/bin/bash

home_dir="/home/ubuntu"
output_file="$home_dir/output.log"

AMI_ID=$(curl http://169.254.169.254/latest/meta-data/ami-id)
INSTANCE_ID=$(curl http://169.254.169.254/latest/meta-data/instance-id)
HOSTNAME=$(curl http://169.254.169.254/latest/meta-data/hostname)
AWS_REGION=$(curl http://169.254.169.254/latest/meta-data/placement/region)
INSTANCE_TYPE=$(curl http://169.254.169.254/latest/meta-data/instance-type)
PUBLIC_IP=$(curl http://169.254.169.254/latest/meta-data/public-ipv4)
ACCOUNT_ID=$(curl http://169.254.169.254/latest/meta-data/identity-credentials/ec2/info | jq -r .AccountId)

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

    # Assuming your variables are properly defined
    json_data=$(jq -n \
        --arg topic "$topic" \
        --arg msg "$_msg" \
        --arg title "$_title" \
        --arg click "$_click" \
        --arg _project_link "$_project_link" \
        --arg _pulumi "$_pulumi" \
        --arg _web_url "$_web_url" \
        '{
            topic: $topic,
            message: $msg,
            title: $title,
            tags: ["package"],
            priority: 4,
            click: $click,
            actions: [
                {action: "view", label: "Open GitHub", url: $_project_link, clear: false},
                {action: "view", label: "View Pulumi", url: $pulumi, clear: false},
                {action: "view", label: "View Website", url: $web_url, clear: false}
            ]
        }')

    curl -X POST -H "Content-Type: application/json" -d "$json_data" https://ntfy.sh
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
    echo "[ log ] $1" | tee -a $output_file
}

run() {
    start=$(date +%s.%N);
    # shellcheck disable=SC2048
    $*
    end=$(date +%s.%N);
    _time_diff=$(echo "$end - $start" | bc);
    echo "[ run ] $* took $_time_diff secs" | tee -a "$output_file"
}

main() {
    start_time=$(date +%s.%N);
    log "start_notify()";
    run start_notify;
    log "setup_instance()";
    if run setup_instance; then
        log "success_notify()";
        run success_notify;
    else
        log "failure_notify()";
        run failure_notify;
    fi
    end_time=$(date +%s.%N);
    time_diff=$(echo "$end_time - $start_time" | bc);
    log "end_notify()";
    run end_notify "$time_diff";
}

main
