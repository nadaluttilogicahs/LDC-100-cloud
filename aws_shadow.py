# Fonte: https://github.com/aws/aws-iot-device-sdk-python-v2 
# Data: 2023
# Note: adattato. Aggiornare a sorgenti attuali come per modulo aws_kiobs.py


# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0.

import argparse
from awscrt import auth, io, mqtt, http
from awsiot import iotshadow
from awsiot import mqtt_connection_builder
from concurrent.futures import Future
import sys
import threading
import traceback
from uuid import uuid4

import json

import aws_connect
import shadow_man

# - Overview -
# This sample uses the AWS IoT Device Shadow Service to keep a property in
# sync between device and server. Imagine a light whose color may be changed
# through an app, or set by a local user.
#
# - Instructions -
# Once connected, type a value in the terminal and press Enter to update
# the property's "reported" value. The sample also responds when the "desired"
# value changes on the server. To observe this, edit the Shadow document in
# the AWS Console and set a new "desired" value.
#
# - Detail -
# On startup, the sample requests the shadow document to learn the property's
# initial state. The sample also subscribes to "delta" events from the server,
# which are sent when a property's "desired" value differs from its "reported"
# value. When the sample learns of a new desired value, that value is changed
# on the device and an update is sent to the server with the new "reported"
# value.

# Using globals to simplify sample code
# is_sample_done = threading.Event()

# mqtt_connection = None
shadow_client = None
thing_name = None

shadow_property = "color"
SHADOW_VALUE_DEFAULT = "off"
received_count = 0

class LockedData:
    def __init__(self):
        self.lock = threading.Lock()
        self.shadow_value = None
        self.disconnect_called = False

locked_data = LockedData()

# Function for gracefully quitting this sample
def exit(msg_or_exception):
    if isinstance(msg_or_exception, Exception):
        print("Exiting sample due to exception.")
        traceback.print_exception(msg_or_exception.__class__, msg_or_exception, sys.exc_info()[2])
    else:
        print("Exiting sample:", msg_or_exception)

    # with locked_data.lock:
    #     if not locked_data.disconnect_called:
    #         print("Disconnecting...")
    #         locked_data.disconnect_called = True
    #         future = mqtt_connection.disconnect()
    #         future.add_done_callback(on_disconnected)

def on_disconnected(disconnect_future):
    # # type: (Future) -> None
    # print("Disconnected.")

    # # Signal that sample is finished
    # is_sample_done.set()
    
    print("Shadows instance disconected.")


def on_get_shadow_accepted(response):
    # type: (iotshadow.GetShadowResponse) -> None
    try:
        print("Finished getting initial shadow state.")

        with locked_data.lock:
            if locked_data.shadow_value is not None:
                print("  Ignoring initial query because a delta event has already been received.")
                return

        if response.state:
            if response.state.delta:
                value = response.state.delta.get(shadow_property)
                if value:
                    print("  Shadow contains delta value '{}'.".format(value))
                    change_shadow_value(value)
                    return

            if response.state.reported:
                value = response.state.reported.get(shadow_property)
                if value:
                    print("  Shadow contains reported value '{}'.".format(value))
                    set_local_value_due_to_initial_query(response.state.reported[shadow_property])
                    return

        print("  Shadow document lacks '{}' property. Setting defaults...".format(shadow_property))
        change_shadow_value(SHADOW_VALUE_DEFAULT)
        return

    except Exception as e:
        exit(e)

def on_get_shadow_rejected(error):
    # type: (iotshadow.ErrorResponse) -> None
    if error.code == 404:
        print("Thing has no shadow document. Creating with defaults...")
        change_shadow_value(SHADOW_VALUE_DEFAULT)
    else:
        exit("Get request was rejected. code:{} message:'{}'".format(
            error.code, error.message))

def on_shadow_delta_updated(delta):
    # type: (iotshadow.ShadowDeltaUpdatedEvent) -> None
    print("---------------------------------------------------------------------------------------------------------")
    print(delta.state)
    try:
        print("Received shadow delta event.")
        # _jsonTodb.updateDbFromCloud(delta.state)
        if delta.state and (shadow_property in delta.state):
            value = delta.state[shadow_property]
            if value is None:
                print("  Delta reports that '{}' was deleted. Resetting defaults...".format(shadow_property))
                change_shadow_value(SHADOW_VALUE_DEFAULT)
                return
            else:
                print("  Delta reports that desired value is '{}'. Changing local value...".format(value))
                change_shadow_value(value)
        else:
            print("  Delta did not report a change in '{}'".format(shadow_property))

    except Exception as e:
        exit(e)

def on_publish_update_shadow(future):
    #type: (Future) -> None
    try:
        future.result()
        print("Update request published.")
    except Exception as e:
        print("Failed to publish update request.")
        exit(e)

def on_update_shadow_accepted(response):
    # type: (iotshadow.UpdateShadowResponse) -> None
    try:
        #print("Finished updating reported shadow value to '{}'.".format(response.state.reported[shadow_property])) # type: ignore
        print("Finished updating reported shadow value to '{}'.".format(response.state.reported)) # type: ignore
        #print("Enter desired value: ") # remind user they can input new values
    except:
        exit("Updated shadow is missing the target property.")

def on_update_shadow_rejected(error):
    # type: (iotshadow.ErrorResponse) -> None
    exit("Update request was rejected. code:{} message:'{}'".format(
        error.code, error.message))

def set_local_value_due_to_initial_query(reported_value):
    with locked_data.lock:
        locked_data.shadow_value = reported_value
    print("Enter desired value: ") # remind user they can input new values

def change_shadow_value(value):
    with locked_data.lock:
        if locked_data.shadow_value == value:
            print("Local value is already '{}'.".format(value))
            print("Enter desired value: ") # remind user they can input new values
            return

        print("Changed local shadow value to '{}'.".format(value))
        locked_data.shadow_value = value

    print("Updating reported shadow value to '{}'...".format(value))
    request = iotshadow.UpdateShadowRequest(
        thing_name=thing_name,
        state=iotshadow.ShadowState(
            reported={ shadow_property: value },
            desired={ shadow_property: value }
        )
    )
    future = shadow_client.publish_update_shadow(request, mqtt.QoS.AT_LEAST_ONCE)
    future.add_done_callback(on_publish_update_shadow)


#def shadowUpdate(shadowName, tableName, tablejs, init):                                                    :( json array; see shadowUpdateSingleDict()
def shadowUpdate(shadowName, tableName, tablejs, init, id):                                                 # :) json object
    shadow_name = shadowName

    if init:
        # state=iotshadow.ShadowState(reported={tableName: tablejs})                                        :( json array; see shadowUpdateSingleDict()
        state=iotshadow.ShadowState(reported={tableName:{id: tablejs}})                                     # :) json object
    else:
        #state=state=iotshadow.ShadowState(desired={tableName: tablejs}, reported={tableName: tablejs})     :( json array; see shadowUpdateSingleDict()
        state=state=iotshadow.ShadowState(desired={tableName:{id: tablejs}}, reported={tableName:{id: tablejs}})# :) json object

    if (shadowName == "settings"):
        request = iotshadow.UpdateNamedShadowRequest(
            shadow_name=shadow_name,
            thing_name=thing_name,
            state=state
        )
        #print("Updating desired shadow value to '{}':'{}'...".format(tableName,tablejs))
    else:
        request = iotshadow.UpdateNamedShadowRequest(
            shadow_name=shadow_name,
            thing_name=thing_name,
            # state=iotshadow.ShadowState(reported={tableName: tablejs})                                    :( json array; see shadowUpdateSingleDict()
            state=iotshadow.ShadowState(reported={tableName:{id: tablejs}})                                 # :) json object
        )
    #print("Updating reported shadow value to '{}':'{}'...".format(tableName,tablejs))
      
    # future = shadow_client.publish_update_shadow(request, mqtt.QoS.AT_LEAST_ONCE)
    future = shadow_client.publish_update_named_shadow(request, mqtt.QoS.AT_LEAST_ONCE)
    future.add_done_callback(on_publish_update_shadow)
    # Wait for subscriptions to succeed
    future.result()


def shadowUpdateArray(shadowName, tableName, tablejs, init):
    shadow_name = shadowName

    # Se tableName è None → assume che tablejs sia già un dict con struttura completa (come {rtd: {...}, sets_work: {...}, ...})
    if tableName is None:
        reported_block = tablejs  # già in forma completa
    else:
        reported_block = {tableName: tablejs}

    if init:
        state = iotshadow.ShadowState(
            desired=reported_block,
            reported=reported_block
        )
    else:
        state = iotshadow.ShadowState(reported=reported_block)

    request = iotshadow.UpdateNamedShadowRequest(
        shadow_name=shadow_name,
        thing_name=thing_name,
        state=state
    )

    # MQTT publish
    future = shadow_client.publish_update_named_shadow(request, mqtt.QoS.AT_LEAST_ONCE)
    future.add_done_callback(on_publish_update_shadow)
    future.result()
    
# def shadowUpdateArray(shadowName, tableName, tablejs, init):                                               #:( json array; see shadowUpdateSingleDict()
#     shadow_name = shadowName

#     if init:
#         state=iotshadow.ShadowState(reported={tableName: tablejs})                                         #:( json array; see shadowUpdateSingleDict()
#     else:
#         state=state=iotshadow.ShadowState(desired={tableName: tablejs}, reported={tableName: tablejs})     #:( json array; see shadowUpdateSingleDict()

#     if (shadowName == "settings"):
#         request = iotshadow.UpdateNamedShadowRequest(
#             shadow_name=shadow_name,
#             thing_name=thing_name,
#             state=state
#         )
#         #print("Updating desired shadow value to '{}':'{}'...".format(tableName,tablejs))
#     else:
#         request = iotshadow.UpdateNamedShadowRequest(
#             shadow_name=shadow_name,
#             thing_name=thing_name,
#             state=iotshadow.ShadowState(reported={tableName: tablejs})                                    #:( json array; see shadowUpdateSingleDict()
#         )
#     #print("Updating reported shadow value to '{}':'{}'...".format(tableName,tablejs))
      
#     # future = shadow_client.publish_update_shadow(request, mqtt.QoS.AT_LEAST_ONCE)
#     future = shadow_client.publish_update_named_shadow(request, mqtt.QoS.AT_LEAST_ONCE)
#     future.add_done_callback(on_publish_update_shadow)
#     # Wait for subscriptions to succeed
#     future.result()


def deleteShadow(shadowName):
    print("Delete shadow...")
    shadow_client.publish_delete_named_shadow(
        request=iotshadow.DeleteNamedShadowRequest(thing_name, shadowName, thing_name),
        qos=mqtt.QoS.AT_LEAST_ONCE)


def shadowInit (mqtt_connection, lthing_name):

    global thing_name
    thing_name = lthing_name

    global shadow_client
    shadow_client = iotshadow.IotShadowClient(mqtt_connection)

    try:
        # shadow_name="settings"

        # # Subscribe to necessary topics.
        # # Note that is **is** important to wait for "accepted/rejected" subscriptions
        # # to succeed before publishing the corresponding "request".
        # print("Subscribing to Delta events...")
        # delta_subscribed_future, _ = shadow_client.subscribe_to_named_shadow_delta_updated_events(
        #     request=iotshadow.NamedShadowDeltaUpdatedSubscriptionRequest(shadow_name,thing_name),
        #     qos=mqtt.QoS.AT_LEAST_ONCE,
        #     callback=on_shadow_delta_updated)

        # # Wait for subscription to succeed
        # delta_subscribed_future.result()

        # print("Subscribing to Update responses...")
        # update_accepted_subscribed_future, _ = shadow_client.subscribe_to_update_named_shadow_accepted(
        #     request=iotshadow.UpdateNamedShadowSubscriptionRequest(shadow_name,thing_name),
        #     qos=mqtt.QoS.AT_LEAST_ONCE,
        #     callback=on_update_shadow_accepted)

        # update_rejected_subscribed_future, _ = shadow_client.subscribe_to_update_named_shadow_rejected(
        #     request=iotshadow.UpdateNamedShadowSubscriptionRequest(shadow_name,thing_name),
        #     qos=mqtt.QoS.AT_LEAST_ONCE,
        #     callback=on_update_shadow_rejected)

        # # Wait for subscriptions to succeed
        # update_accepted_subscribed_future.result()
        # update_rejected_subscribed_future.result()

        # print("Subscribing to Get responses...")
        # get_accepted_subscribed_future, _ = shadow_client.subscribe_to_get_named_shadow_accepted(
        #     request=iotshadow.GetNamedShadowSubscriptionRequest(shadow_name,thing_name),
        #     qos=mqtt.QoS.AT_LEAST_ONCE,
        #     callback=on_get_shadow_accepted)

        # get_rejected_subscribed_future, _ = shadow_client.subscribe_to_get_named_shadow_rejected(
        #     request=iotshadow.GetNamedShadowSubscriptionRequest(shadow_name,thing_name),
        #     qos=mqtt.QoS.AT_LEAST_ONCE,
        #     callback=on_get_shadow_rejected)

        # # Wait for subscriptions to succeed
        # get_accepted_subscribed_future.result()
        # get_rejected_subscribed_future.result()

        # print("Delete shadow...")
        # shadow_client.publish_delete_named_shadow(
        #     request=iotshadow.DeleteNamedShadowRequest(thing_name, shadow_name, thing_name),
        #     qos=mqtt.QoS.AT_LEAST_ONCE)

        # shadow_name="rtd"
 
        # print("Subscribing to Update responses...")
        # update_accepted_subscribed_future, _ = shadow_client.subscribe_to_update_named_shadow_accepted(
        #     request=iotshadow.UpdateNamedShadowSubscriptionRequest(shadow_name,thing_name),
        #     qos=mqtt.QoS.AT_LEAST_ONCE,
        #     callback=on_update_shadow_accepted)

        # update_rejected_subscribed_future, _ = shadow_client.subscribe_to_update_named_shadow_rejected(
        #     request=iotshadow.UpdateNamedShadowSubscriptionRequest(shadow_name,thing_name),
        #     qos=mqtt.QoS.AT_LEAST_ONCE,
        #     callback=on_update_shadow_rejected)

        # # Wait for subscriptions to succeed
        # update_accepted_subscribed_future.result()
        # update_rejected_subscribed_future.result()

        # print("Delete shadow...")
        # shadow_client.publish_delete_named_shadow(
        #     request=iotshadow.DeleteNamedShadowRequest(thing_name, shadow_name, thing_name),
        #     qos=mqtt.QoS.AT_LEAST_ONCE)
        

        for item in shadow_man.ShadowsToDel:
            print(f"Delete shadow...{item}")
            shadow_client.publish_delete_named_shadow(
                request=iotshadow.DeleteNamedShadowRequest(thing_name, item, thing_name),
                qos=mqtt.QoS.AT_LEAST_ONCE)

    except Exception as e:
        exit(e)

