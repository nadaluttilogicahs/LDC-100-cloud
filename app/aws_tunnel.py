import json
from . import aws_connect

# Callback per la ricezione delle notifiche del tunnel
def on_tunnel_notification(topic, payload, **kwargs):
    print(f"Received message from {topic}: {payload}")
    data = json.loads(payload)
    client_access_token = data['clientAccessToken']
    endpoint = data['region']  # Endpoint del tunnel
    print(f"Client access token: {client_access_token}")
    print(f"Tunnel endpoint: {endpoint}")
    connect_to_tunnel(client_access_token, endpoint)

# Funzione per stabilire la connessione al tunnel
# def connect_to_tunnel(client_access_token, endpoint):
#     import subprocess
#     # Comando per usare SSH attraverso il tunnel
#     tunnel_command = [
#         "ssh",
#         "-o", f"ProxyCommand=wscat --connect wss://{'data.tunneling.iot.eu-central-1.amazonaws.com'} --header 'x-amzn-iot-securetunneling-access-token: {client_access_token}'",
#         "localhost"
#     ]
#     # Esegui il comando
#     subprocess.run(tunnel_command)

def connect_to_tunnel(client_access_token, region="eu-central-1"):
    import subprocess
    
    cmd = f'aws-iot-secure-tunnel-cli -t {client_access_token} -r {region}'
    subprocess.Popen(cmd, shell=True)

    # # Comando per avviare il proxy locale utilizzando Docker
    # proxy_command = [
    #     "sudo", "docker", "run", "--rm", "-it", "--network=host",
    #     # "sudo", "docker", "run", "--rm", "--platform linux/arm64", "-it", "--network=host",
    #     "-v", "/etc/ssl/certs:/etc/ssl/certs:ro",
    #     # "public.ecr.aws/aws-iot-securetunneling-localproxy/debian-bin:arm64-latest",
    #     "public.ecr.aws/aws-iot-securetunneling-localproxy/ubuntu-bin:armv7-latest",
    #     # "public.ecr.aws/aws-iot-securetunneling-localproxy/ubuntu-bin:arm64-latest",
    #     "--region", region,
    #     "-t", client_access_token,
    #     "--mode", "destination",
    #     "-d", "22",
    # ]

    # try:
    #     # Avvia il proxy locale in un processo separato
    #     proxy_process = subprocess.Popen(proxy_command)

    #     print("Local proxy avviato. In attesa che il tunnel sia pronto...")

    #     # Comando SSH per connettersi tramite il tunnel
    #     ssh_command = [
    #         "ssh",
    #         "-o", "StrictHostKeyChecking=no",
    #         "-o", "UserKnownHostsFile=/dev/null",
    #         "-p", "22",  # Porta utilizzata dal proxy locale
    #         "localhost"
    #     ]
        
    #     # Connettersi tramite SSH
    #     subprocess.run(ssh_command)
    
    # finally:
    #     # Termina il proxy locale quando hai finito
    #     proxy_process.terminate()
    #     proxy_process.wait()
    #     print("Local proxy terminato.")

def tunnelInit (mqtt_connection, lthing_name):

    NOTIFY_TOPIC = f"$aws/things/{lthing_name}/tunnels/notify"
    mqtt_connection.subscribe(NOTIFY_TOPIC, mqtt.QoS.AT_LEAST_ONCE, on_tunnel_notification)