#!/usr/bin/env python3
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
# import _sqlite
# import _def
from _python_com import _sqlite, _def

import json
import aws_connect


work_dir = _def.work_dir
dbd = work_dir + _def.DB_SET_D


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
    print ("Got a request!")
    endIdxChr = myString.find(' @')
    query = myString[startIdxChr+4:endIdxChr]
    lenStr = len(myString)
    # db = myString[endIdxChr+2:lenStr-1]
    db = myString[endIdxChr+2:lenStr]
    print (query)

    if db == 'rtd':
        db = work_dir + _def.DB_RTD_D
    elif db == 'settings':
        db = work_dir + _def.DB_SET_D        
    elif db == 'prg':
        db = work_dir + _def.DB_PRG_D
    elif db == 'language':
        db = work_dir + _def.DB_LAN_D
    elif db == '':
        db = 'NONE'
    else:
        db = work_dir + _def.DB_ARC_D + db + '.db'

    if db != 'NONE':
        if query.find('SELECT') >= 0:
            jsonDB =_sqlite.select_task_by_query(db, query)
            # ret = bytes(json.dumps(jsonDB), 'utf-8')
            ret = jsonDB
        #elif query.find('UPDATE') >= 0 or query.find('INSERT') >= 0 or query.find('REPLACE') >= 0 or query.find('CREATE TABLE') >= 0:
        elif query.find('UPDATE') >= 0 or query.find('INSERT') >= 0 or query.find('REPLACE') >= 0:
            jsonDB =_sqlite.update_task_by_query(db, query)
            if jsonDB != []:
                ret = bytes(jsonDB, 'utf-8')      # !! ritorna stringa errore !!
            else:
                ret = 'DONE'
        else:
        #elif query.find('CREATE TABLE') >= 0:
            jsonDB =_sqlite.update_task_by_query(db, query)
            if jsonDB != []:
                ret = bytes(jsonDB, 'utf-8')      # !! ritorna stringa errore !!
            else:
                ret = 'DONE'
        # else:
        #     ret = b'no valid command'
        #     print(ret)
    else:
        ret = b'no exiting DB'
        print(ret)

    # ret_str = ret.decode('utf-8')
    aws_connect.publicMessage(idApp, idMsg, ret)

    return ret




