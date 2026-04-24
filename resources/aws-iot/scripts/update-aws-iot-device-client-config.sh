#!/bin/bash

CONFIG_FILE="/opt/aws-iot/config/aws-iot-device-client-config.json"
ENDPOINT_FILE="/opt/aws-iot/device-info/endpoint.txt"
THING_NAME_FILE="/opt/aws-iot/device-info/device_id.txt"

# Verifica che i file esistano prima di procedere
if [[ ! -f "$ENDPOINT_FILE" ]]; then
    echo "❌ Errore: Il file $ENDPOINT_FILE non esiste!"
    exit 1
fi

if [[ ! -f "$THING_NAME_FILE" ]]; then
    echo "❌ Errore: Il file $THING_NAME_FILE non esiste!"
    exit 1
fi

# Legge i valori dai file di testo
ENDPOINT=$(cat "$ENDPOINT_FILE" | tr -d ' \t\n\r')
THING_NAME=$(cat "$THING_NAME_FILE" | tr -d ' \t\n\r')

# Sostituisce i valori nel file di configurazione JSON
sed -i "s|\"endpoint\": \".*\"|\"endpoint\": \"$ENDPOINT\"|" "$CONFIG_FILE"
sed -i "s|\"thing-name\": \".*\"|\"thing-name\": \"$THING_NAME\"|" "$CONFIG_FILE"

echo "✅ Configurazione aggiornata: endpoint=$ENDPOINT, thing-name=$THING_NAME"


