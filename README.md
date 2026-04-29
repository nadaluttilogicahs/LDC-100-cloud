# LDC-100 cloud service

Servizio systemd per interfaccia cloud di sistemi LDC-100

## Installazione
```bash
git clone git@github.com:nadaluttilogicahs/LDC-100-cloud.git
cd LDC-100-cloud
sudo ./install.sh
```
Lo script di installazione installerà e avvierà il processo systemd. Copia inoltre nella cartella `/home/lg58/LDC-100/cloud` il contenuto della presente cartella.
Crea anche l'ambiente virtuale necessario all'esecuzione del software.

## Struttura

```
/home/lg58/LDC-100/cloud/
├── resources/
│   ├── app/        
│       └── ...
│   ├── systemd/
│       └── ...
│   ├── __version__.py
│   └── de01cloud.py    # Launcher python dell'applicazione
├── .venv
├── systemd_cloud.sh    # Script che lancia il launcher python (utilizzato da servizio systemd)
...
```
## Comandi Utili

```bash
# Stato servizio
sudo systemctl status ldc-100-cloud

# Riavvia servizio
sudo systemctl restart ldc-100-cloud

# Ferma servizio
sudo systemctl stop ldc-100-cloud

# Visualizza log in tempo reale
sudo journalctl -u ldc-100-cloud -f

# Visualizza log completo
sudo journalctl -u ldc-100-cloud --no-pager

# Disabilita avvio automatico
sudo systemctl disable ldc-100-cloud

# Riabilita avvio automatico
sudo systemctl enable ldc-100-cloud

# Rimuovi vecchio servizio
sudo systemctl stop ldc-100-cloud
sudo systemctl disable ldc-100-cloud
sudo rm /etc/systemd/system/ldc-100-cloud.service
```

## Licenza

Proprietario: Logica H&S Srl

## Contatti

Per supporto tecnico contattare Logica H&S Srl.