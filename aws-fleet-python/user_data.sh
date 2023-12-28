#!/bin/bash
echo "Hello, World from Pulumi!" > index.html
nohup python3 -m http.server 80 &
