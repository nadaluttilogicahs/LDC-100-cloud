# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0.
import os
import sys

from ldc_common._paths import PATHS
from ldc_common import _sqlite

import argparse
from awscrt import auth, io, mqtt, http
from awsiot import iotshadow
from awsiot import mqtt_connection_builder
from concurrent.futures import Future
import threading
import traceback
from uuid import uuid4

import json
import pdb
import time
# import aws_jobs
from . import aws_shadow
from . import pubsub_man
from awscrt.mqtt import Will, QoS


certs_dir = PATHS.certs_dir
dev_info_dir = PATHS.dev_info_dir


# Using globals to simplify sample code
is_sample_done = threading.Event()

mqtt_connection = None
# thing_name = ""
received_count = 0

class LockedData:
    def __init__(self):
        self.lock = threading.Lock()
        self.shadow_value = None
        self.disconnect_called = False

locked_data = LockedData()


"""
===========================================================================
Funzioni di gestione aws PubSub. Qui invece che in un modulo aws_pubsub.py
aprire altre istanze della connessione mqtt
"""
# Callback when the subscribed topic receives a message
def on_message_received(topic, payload, dup, qos, retain, **kwargs):
    time.sleep(0.5) 
    print("Received message from topic '{}': {}".format(topic, payload))
    global received_count
    received_count += 1
    pubsub_man.awsSqlQuery(payload)
    # if received_count == cmdData.input_count:
    #     received_all_event.set()

def publicMessage (idApp, idMsg, response):

    # Publish
    if idApp == "":
        TOPIC = "devices/" + thing_name + "/sql/response"
    else:
        TOPIC = "devices/" + thing_name + "/sql/" + idApp + "/response"
    print(f"Publishing message to topic {TOPIC}...")

    message_dict = {
        "idMsg": idMsg,
        "msg": response
    }
    message_json = json.dumps(message_dict)  # str
    # message_json = response

    print(message_json)

    global mqtt_connection
    mqtt_connection.publish(
        topic=TOPIC,
        # payload=f"{ {response} }",
        # payload=response,
        payload = message_json,

        # qos=mqtt.QoS.AT_LEAST_ONCE
        qos=mqtt.QoS.AT_MOST_ONCE
    )
    print("Message published!")

"""
===========================================================================
"""


# Function for gracefully quitting this sample
def exit(msg_or_exception):
    if isinstance(msg_or_exception, Exception):
        print("Exiting sample due to exception.")
        traceback.print_exception(msg_or_exception.__class__, msg_or_exception, sys.exc_info()[2])
    else:
        print("Exiting sample:", msg_or_exception)

    with locked_data.lock:
        if not locked_data.disconnect_called:
            print("Disconnecting...")
            locked_data.disconnect_called = True
            future = mqtt_connection.disconnect()
            future.add_done_callback(on_disconnected)

def on_disconnected(disconnect_future):
    # type: (Future) -> None
    print("Disconnected.")

    # Signal that sample is finished
    is_sample_done.set()


# Fonte: https://github.com/aws/aws-iot-device-sdk-python-v2/blob/main/samples/pubsub.py
# Data: 03/02/2025
# Note: 

# Callback when connection is accidentally lost.
def on_connection_interrupted(connection, error, **kwargs):
    print("Connection interrupted. error: {}".format(error))

# Callback when an interrupted connection is re-established.
def on_connection_resumed(connection, return_code, session_present, **kwargs):
    print("Connection resumed. return_code: {} session_present: {}".format(return_code, session_present))

    if return_code == mqtt.ConnectReturnCode.ACCEPTED and not session_present:
        print("Session did not persist. Resubscribing to existing topics...")
        resubscribe_future, _ = connection.resubscribe_existing_topics()

        # Cannot synchronously wait for resubscribe result because we're on the connection's event-loop thread,
        # evaluate result with a callback instead.
        resubscribe_future.add_done_callback(on_resubscribe_complete)

def on_resubscribe_complete(resubscribe_future):
    resubscribe_results = resubscribe_future.result()
    print("Resubscribe results: {}".format(resubscribe_results))

    for topic, qos in resubscribe_results['topics']:
        if qos is None:
            sys.exit("Server rejected resubscribe to topic: {}".format(topic))

# Callback when the connection successfully connects
def on_connection_success(connection, callback_data):
    assert isinstance(callback_data, mqtt.OnConnectionSuccessData)
    print("Connection Successful with return code: {} session present: {}".format(callback_data.return_code, callback_data.session_present))

# Callback when a connection attempt fails
def on_connection_failure(connection, callback_data):
    assert isinstance(callback_data, mqtt.OnConnectionFailureData)
    print("Connection failed with error code: {}".format(callback_data.error))

# Callback when a connection has been disconnected or shutdown successfully
def on_connection_closed(connection, callback_data):
    print("Connection closed")

    

def connect():
    global thing_name

    # Configure your AWS IoT Thing details
    root_ca_path = os.path.join(certs_dir, "AmazonRootCA1.pem")
    certificate_path = os.path.join(certs_dir, "certificate.pem.crt")
    private_key_path = os.path.join(certs_dir, "private.pem.key")
    device_id_path = os.path.join(dev_info_dir, "device_id.txt")
    endpoint_path = os.path.join(dev_info_dir, "endpoint.txt")

    with open (device_id_path, "r") as myfile:
        thing_name = myfile.read()
    with open (endpoint_path, "r") as myfile:
        endpoint = myfile.read()

    # aggiungo una T (telemetry) visto client_id=thing_name già utilizzato dalla connessione mqtt di aws-iot-device-client, utilizza per Jobs e altri servizi di "service"
    client_id=thing_name + "T"

    # Spin up resources
    event_loop_group = io.EventLoopGroup(1)
    host_resolver = io.DefaultHostResolver(event_loop_group)
    client_bootstrap = io.ClientBootstrap(event_loop_group, host_resolver)
        
    # Costruisci il messaggio di Will: pubblicherà su un topic dedicato
    will_topic   = f"devices/lwt/{client_id}"
    will_payload = json.dumps({
        "clientId": client_id,
        "event":    "offline"
    }).encode('utf-8')
    will_qos     = QoS.AT_LEAST_ONCE

    will = Will(
        topic=will_topic,
        payload=will_payload,
        qos=will_qos,
        retain=False
    )
    
    global mqtt_connection
    mqtt_connection = mqtt_connection_builder.mtls_from_path(
        endpoint=endpoint,
        cert_filepath=certificate_path,
        pri_key_filepath=private_key_path,
        client_bootstrap=client_bootstrap,
        ca_filepath=root_ca_path,
        client_id=client_id,
        
        clean_session=False,        # sessione persistente
        keep_alive_secs=120,        # ping ogni 120s
        will=will,                  # il Will creato sopra
        will_delay_seconds=30,      # <-- qui, non nel Will!
        
        # 4) callback esistenti
        on_connection_interrupted=on_connection_interrupted,
        on_connection_resumed=on_connection_resumed,
        on_connection_success=on_connection_success,
        on_connection_failure=on_connection_failure,
        on_connection_closed=on_connection_closed)

    print("Connecting to {} with client ID '{}'...".format(
        endpoint, client_id))

    connected_future = mqtt_connection.connect()

    # Wait for connection to be fully established.
    # Note that it's not necessary to wait, commands issued to the
    # mqtt_connection before its fully connected will simply be queued.
    # But this sample waits here so it's obvious when a connection
    # fails or succeeds.
    connected_future.result()
    print("Connected!")

    try:

        ############################################################
        # Pubsub
        message_topic = f"devices/{thing_name}/sql/query"

        # Subscribe
        print("Subscribing to topic '{}'...".format(message_topic))
        subscribe_future, packet_id = mqtt_connection.subscribe(
            topic=message_topic,
            # qos=mqtt.QoS.AT_LEAST_ONCE,
            qos=mqtt.QoS.AT_MOST_ONCE,
            callback=on_message_received)
        
        subscribe_future.result()
        print("Subscribed topic '{}'!".format(message_topic))

        publicMessage("", "", "Test pubblic message")

        ############################################################

        aws_shadow.shadowInit(mqtt_connection, thing_name)
        
        # jobs gestiti con aws-iot-device-client con altra connessione mqtt
        ##aws_jobs.jobInit(mqtt_connection, thing_name)
    except Exception as e:
        exit(e)
