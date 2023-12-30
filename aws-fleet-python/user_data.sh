#!/bin/bash

home_dir="/home/ubuntu"
output_file="$home_dir/output.log"

run() {
    # shellcheck disable=SC2145
    echo "Running: $@"
    # shellcheck disable=SC2145
    "$@ | tee -a $output_file"
}

run cd $home_dir || exit
sudo apt-get update -y && sudo apt-get install -y python3-pip || echo "Failed to install python3-pip"
echo "Hello, World from Pulumi!" > index.html
nohup python3 -m http.server 80 > file.txt 2>&1 &
cd - || exit