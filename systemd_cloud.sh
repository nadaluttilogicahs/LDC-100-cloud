#!/bin/bash

DIR="$(dirname "$0")"

if [ ! -d "$DIR/.venv" ]; then
    python -m venv "$DIR/.venv"
    "$DIR/.venv/bin/pip" install --no-index \
        --find-links="$DIR/pyPackages/" \
        -r "$DIR/requirements.txt"
fi

source "$DIR/.venv/bin/activate"
cd "$DIR/resources"
exec python3 de01cloud.py