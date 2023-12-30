#!/bin/bash

home_dir="/home/ubuntu"
output_file="$home_dir/output.log"
docker_vol="$home_dir/docker_volume"
run() {
    # shellcheck disable=SC2145
    echo "Running: $@"
    # shellcheck disable=SC2145
    "$@ | tee -a $output_file"
}

cd $home_dir || exit
sudo apt-get update -y
sudo apt-get install -y python3-pip docker.io
echo "Hello, World from Pulumi!" > index.html
run nohup python3 -m http.server 80 > file.txt 2>&1 &
mkdir -p $home_dir/docker_volume
run docker run --network=host -v $docker_vol:/dev/shm -d --name graphstorm mohammadzainabbas/graphstorm:local || echo "Failed to run docker container"
cd - || exit