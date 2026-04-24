#!/usr/bin/env python3
import sys
import os

import json
from . import aws_connect
from .data_man import query_db


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

    # PROCESS RECEIVING DATA
    startIdxChr = message.find('SQL')
    if startIdxChr == -1:
        print("INVALID COMMAND")
        # self.request.sendall(b'INVALID COMMAND')
        return
    
    procSqlQuery(idApp, idMsg, message, startIdxChr)


def procSqlQuery (idApp, idMsg, myString, startIdxChr):
    print("Got a request!")
    endIdxChr = myString.find(' @')
    query = myString[startIdxChr + 4:endIdxChr]
    db_tag = myString[endIdxChr + 2:].strip()

    ret = query_db(db_tag, query)
    aws_connect.publicMessage(idApp, idMsg, ret)
    return ret



