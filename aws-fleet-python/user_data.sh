#!/bin/bash

cd /home/ubuntu || exit
sudo apt-get update -y && sudo apt-get install -y python3-pip || echo "Failed to install python3-pip"
echo "Hello, World from Pulumi!" > index.html
nohup python3 -m http.server 80 &
cd - || exit