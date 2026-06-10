#!/usr/bin/env python3
import sys
import os

import json
import threading
from . import aws_connect
from .data_man import query_db
import httpx                          # pip install httpx


FASTAPI_BASE = "http://localhost:8000"

def awsSqlQuery (paylod):
    print("Raw paylod", paylod)

    # Decodifica il byte string in una stringa JSON
    decoded_data = paylod.decode('utf-8')

    # Parsea la stringa JSON in un dizionario
    parsed_data = json.loads(decoded_data)

    # Estrai il valore del campo "idApp"
    idApp = parsed_data.get("idApp", "")
    print("ID app: ", idApp)
    
    # Estrai il valore del campo "idMsg"
    idMsg = parsed_data.get("idMsg", "")
    print("ID msg: ", idMsg)

    # Estrai il valore del campo "message"
    message = parsed_data.get("message", "")
    print("SQL Query: ", message)

    # # PROCESS RECEIVING DATA
    # startIdxChr = message.find('SQL')
    # if startIdxChr == -1:
    #     print("INVALID COMMAND")
    #     # self.request.sendall(b'INVALID COMMAND')
    #     return
    
    # procSqlQuery(idApp, idMsg, message, startIdxChr)
    
    if message.startswith('API GET '):
        path = message[8:]
        # lancia in thread separato — non blocca il receiver MQTT
        threading.Thread(
            target=_proc_api_get,
            args=(idApp, idMsg, path),
            daemon=True
        ).start()

    elif message.startswith('SQL'):
        startIdxChr = message.find('SQL')
        procSqlQuery(idApp, idMsg, message, startIdxChr)

    else:
        print("INVALID COMMAND:", message)


def procSqlQuery (idApp, idMsg, myString, startIdxChr):
    print("Got a request!")
    endIdxChr = myString.find(' @')
    query = myString[startIdxChr + 4:endIdxChr]
    db_tag = myString[endIdxChr + 2:].strip()

    ret = query_db(db_tag, query)
    aws_connect.publicMessage(idApp, idMsg, ret)
    return ret

def _proc_api_get(idApp, idMsg, path):
    try:
        r = httpx.get(f"{FASTAPI_BASE}{path}", timeout=15)
        r.raise_for_status()
        aws_connect.publicMessage(idApp, idMsg, r.json())
    except Exception as e:
        print(f"API GET error for {path}: {e}")
        aws_connect.publicMessage(idApp, idMsg, {"error": str(e)})

