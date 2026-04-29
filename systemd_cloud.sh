#!/bin/bash

source "$(dirname "$0")/.venv/bin/activate" 
cd "$(dirname "$0")/resources"

python3 de01cloud.py