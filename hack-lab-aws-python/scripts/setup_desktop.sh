#!/bin/bash

home_dir="$HOME"
output_file="$home_dir/output.log"

AMI_ID=$(curl http://169.254.169.254/latest/meta-data/ami-id)
INSTANCE_ID=$(curl http://169.254.169.254/latest/meta-data/instance-id)
HOSTNAME=$(curl http://169.254.169.254/latest/meta-data/hostname)
AWS_REGION=$(curl http://169.254.169.254/latest/meta-data/placement/region)
INSTANCE_TYPE=$(curl http://169.254.169.254/latest/meta-data/instance-type)
PUBLIC_IP=$(curl http://169.254.169.254/latest/meta-data/public-ipv4)
ACCOUNT_ID=$(curl http://169.254.169.254/latest/meta-data/identity-credentials/ec2/info | jq -r .AccountId)

# ------------------------------
# Logging & Run method
# ------------------------------

log() {
    echo "[ log ] $1" | tee -a "$output_file"
}

run() {
    start=$(date +%s.%N);
    # shellcheck disable=SC2048
    $* | tee -a "$output_file"
    exit_code=$?
    end=$(date +%s.%N);
    _time_diff=$(echo "$end - $start" | bc);
    echo "[ run ] $* took $_time_diff secs with exit code $exit_code" | tee -a "$output_file"
    return $exit_code
}

# ------------------------------
# Setup method
# ------------------------------

setup_instance() {
    sudo apt update && sudo apt install -y kali-linux-headless
}

# ------------------------------
# Notify via ntfy.sh
# ------------------------------
topic="mohammadzainabbas-aws"
github="https://github.com/mohammadzainabbas/pulumi-labs"
project="hack-lab-aws-python"
_project_link="$github/tree/main/$project"
_click="$_project_link"
_attach="https://get.pulumi.com/new/button.svg"
_filename="pulumi.svg"
_pulumi="https://app.pulumi.com/mohammadzainabbas/projects"

send_to_ntfy() {
    local json_data=$1
    echo "$json_data" | jq
    curl -X POST -H "Content-Type: application/json" -d "$json_data" https://ntfy.sh
}

start_notify() {
    _title="Deploying '$INSTANCE_TYPE' with '$PUBLIC_IP' IPv4 🦋"
    _msg="Started setup scripts on Instance ID: '$INSTANCE_ID' with AMI: '$AMI_ID' at '$AWS_REGION' by account: '$ACCOUNT_ID' 🚧"
    
    json_data=$(jq -n \
        --arg topic "$topic" \
        --arg msg "$_msg" \
        --arg title "$_title" \
        --arg click "$_click" \
        --arg project_link "$_project_link" \
        --arg pulumi_link "$_pulumi" \
        '{
            topic: $topic,
            message: $msg,
            title: $title,
            tags: ["package"],
            priority: 4,
            click: $click,
            actions: [
                {action: "view", label: "Open GitHub", url: $project_link, clear: false},
                {action: "view", label: "View Pulumi", url: $pulumi_link, clear: false}
            ]
        }')
    send_to_ntfy "$json_data"
}

end_notify() {
    local TIME=$1
    _title="Took $TIME secs to run setup scripts on '$INSTANCE_TYPE' with '$PUBLIC_IP' IPv4 🌟"
    _msg="Setup scripts completed on Instance ID: '$INSTANCE_ID' with AMI: '$AMI_ID' at '$AWS_REGION' by account: '$ACCOUNT_ID' 👨‍💻"
    
    json_data=$(jq -n \
        --arg topic "$topic" \
        --arg msg "$_msg" \
        --arg title "$_title" \
        --arg click "$_click" \
        --arg project_link "$_project_link" \
        --arg pulumi_link "$_pulumi" \
        '{
            topic: $topic,
            message: $msg,
            title: $title,
            tags: ["alarm_clock"],
            priority: 4,
            click: $click,
            actions: [
                {action: "view", label: "Open GitHub", url: $project_link, clear: false},
                {action: "view", label: "View Pulumi", url: $pulumi_link, clear: false}
            ]
        }')
    send_to_ntfy "$json_data"
}

success_notify() {
    _title="Setup deployed on '$INSTANCE_TYPE' with '$PUBLIC_IP' IPv4 🚀"
    _msg="Instance ID: '$INSTANCE_ID' was deployed with AMI: '$AMI_ID' at '$AWS_REGION' by account: '$ACCOUNT_ID' 🚀"
    _web_url="http://$PUBLIC_IP"
    
    json_data=$(jq -n \
        --arg topic "$topic" \
        --arg msg "$_msg" \
        --arg title "$_title" \
        --arg click "$_click" \
        --arg project_link "$_project_link" \
        --arg pulumi_link "$_pulumi" \
        --arg web_link "$_web_url" \
        '{
            topic: $topic,
            message: $msg,
            title: $title,
            tags: ["white_check_mark", "tada"],
            priority: 4,
            click: $click,
            actions: [
                {action: "view", label: "View Website", url: $web_link, clear: false},
                {action: "view", label: "Open GitHub", url: $project_link, clear: false},
                {action: "view", label: "View Pulumi", url: $pulumi_link, clear: false}
            ]
        }')
    send_to_ntfy "$json_data"
}

failure_notify() {
    _title="Unable to deploy setup on '$INSTANCE_TYPE' with '$PUBLIC_IP' IPv4 💔"
    _msg="Debug Info - Instance ID: '$INSTANCE_ID' with AMI: '$AMI_ID' at '$AWS_REGION' by account: '$ACCOUNT_ID' 💔"
    
    json_data=$(jq -n \
        --arg topic "$topic" \
        --arg msg "$_msg" \
        --arg title "$_title" \
        --arg click "$_click" \
        --arg project_link "$_project_link" \
        --arg pulumi_link "$_pulumi" \
        '{
            topic: $topic,
            message: $msg,
            title: $title,
            tags: ["x", "face_with_head_bandage"],
            priority: 5,
            click: $click,
            actions: [
                {action: "view", label: "Open GitHub", url: $project_link, clear: false},
                {action: "view", label: "View Pulumi", url: $pulumi_link, clear: false}
            ]
        }')
    send_to_ntfy "$json_data"
}

# ------------------------------
# main method
# ------------------------------

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
