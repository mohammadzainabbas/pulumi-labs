#!/bin/bash

log() {
    echo "[ log ] $1"
}

main() {
    local url="$1"
    local output_dir="$2"
    local filename="$3"

    cd "$output_dir" || exit 1

    log "Downloading zip file ..."
    wget -q "$url" -O "$filename" || exit 1

    cd - || exit 1

}

main "$@"