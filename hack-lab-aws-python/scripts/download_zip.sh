#!/bin/bash

log() {
    echo "[ log ] $1"
}

main() {
    local output_file="$1" 
    log "Downloading zip file ..."
    wget

}

main "$@"