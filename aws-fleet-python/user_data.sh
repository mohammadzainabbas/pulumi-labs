#!/bin/bash

home_dir="/home/ubuntu"
output_file="$home_dir/output.log"
docker_vol="$home_dir/docker_volume"

cd $home_dir || exit
sudo apt-get update -y | tee -a $output_file
sudo apt-get install -y python3-pip docker.io | tee -a $output_file
echo "Hello, World from Pulumi!" > index.html
nohup python3 -m http.server 80 > file.txt 2>&1 &
mkdir -p $home_dir/docker_volume
sudo systemctl start docker.service
docker run --network=host -v $docker_vol:/dev/shm -d --name graphstorm mohammadzainabbas/graphstorm:local | tee -a $output_file
cd - || exit