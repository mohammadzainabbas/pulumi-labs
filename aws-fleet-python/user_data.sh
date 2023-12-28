#!/bin/bash
echo "Hello, World from Pulumi!" > index.html
nohup python -m http.server 443 &