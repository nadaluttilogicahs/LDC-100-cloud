#!/bin/bash

###############################################################################
# 
# LDC-100 cloud service - Installation Script
# 
###############################################################################

LDC_BASE_DIR="/home/lg58/LDC-100"
SERVICE_NAME="cloud"
SERVICE_DIR="${LDC_BASE_DIR}/${SERVICE_NAME}"
SERVICE_USR="lg58"

if [ "$EUID" -ne 0 ]; then 
    echo "Esegui con sudo: sudo ./install.sh"
    exit 1
fi

sudo -u ${SERVICE_USR} echo "Installazione LDC-100-cloud.service"

sudo -u ${SERVICE_USR} echo "Installazione dipendenze"

apt update
apt install -y python3.13 python3-pip python3.13-venv

sudo -u ${SERVICE_USR} echo "Creazione cartella per file di servizio"
sudo -u ${SERVICE_USR} mkdir -p ${SERVICE_DIR}

sudo -u ${SERVICE_USR} echo "Copia contenuti nella cartella creata"
cp -r * ${SERVICE_DIR}

chown -R ${SERVICE_USR}:${SERVICE_USR} ${SERVICE_DIR}
chmod -R 750 ${LDC_BASE_DIR}

sudo -u ${SERVICE_USR} python3 -m venv ${SERVICE_DIR}/.venv

sudo -u ${SERVICE_USR} echo "Creazione ambiente virtuale Python"
sudo -u ${SERVICE_USR} ${SERVICE_DIR}/.venv/bin/pip install --upgrade pip

sudo -u ${SERVICE_USR} ${SERVICE_DIR}/.venv/bin/pip install -r requirements.txt

chown -R ${SERVICE_USR}:${SERVICE_USR} ${SERVICE_DIR}
chmod -R 750 ${SERVICE_DIR}

echo "Creazione servizio LDC-100-cloud.service"
cp ${SERVICE_DIR}/resources/systemd/ldc-100-cloud.service /etc/systemd/system

echo "Lancio del servizio"
systemctl daemon-reload
systemctl enable --now ldc-100-cloud.service

sudo -u ${SERVICE_USR} sleep 2
sudo -u ${SERVICE_USR} echo "Verifica stato servizio"
systemctl status ldc-100-cloud.service --no-pager

sudo -u ${SERVICE_USR} echo "Installazione LDC-100-cloud.service completata."