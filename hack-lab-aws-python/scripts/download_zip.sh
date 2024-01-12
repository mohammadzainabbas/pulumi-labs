#!/bin/bash

log() {
    echo "[ log ] $1"
}

main() {
    local url="$1"

    log "Downloading zip file ..."
    wget

}

main "$@"