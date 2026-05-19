#!/bin/bash


if [ ! -d $(dirname "$0")/.venv ]; then
  python -m venv .venv
  source "$(dirname "$0")/.venv/bin/activate"
  pip install --no-index --find-links=$(dirname "$0")/pyPackages/ -r requirements.txt

else
  source "$(dirname "$0")/.venv/bin/activate" 
  cd "$(dirname "$0")/resources"

  python3 de01cloud.py

fi