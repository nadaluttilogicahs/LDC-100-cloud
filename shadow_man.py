#!/usr/bin/env python3
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
# import _sqlite
# import _def
from _python_com import _sqlite, _def, _utility

import time
import aws_shadow
#import boto3

DB_SET = _def.work_dir + _def.DB_SET_D
DB_RTD = _def.work_dir + _def.DB_RTD_D

DB_LAN = _def.work_dir + _def.DB_LAN_D
DB_PRG = _def.work_dir + _def.DB_PRG_D

ShadowsToDel = ('alarms', 'cycleInfo', 'mainSets')
# ShadowsToDel = ("alarms")


# def getShadowSize (thing_name, shadow_name):
#     # Initialize the AWS IoT client
#     client = boto3.client('iot-data', region_name='eu-central-1')

#     # Replace with your device's thing name
#     #thing_name = '3500006'

#     # Get the current shadow of the device
#     response = client.get_thing_shadow(thingName=thing_name, shadowName=shadow_name)

#     # The response contains the shadow document in the 'payload' field
#     payload = response['payload'].read()

#     # Convert the payload (bytes) to a string if needed
#     shadow_document = payload.decode('utf-8')

#     # Print the shadow document (JSON)
#     print(shadow_document)

#     # Get the size of the shadow document in bytes
#     size_in_bytes = len(payload)

#     # Alternatively, you can get the size of the shadow document as a string (if you want it in characters)
#     size_in_chars = len(shadow_document)

#     print(f"Size of the shadow document: {size_in_bytes} bytes")
#     print(f"Size of the shadow document: {size_in_chars} characters")



# table_names = _sqlite.select_tables_name(dbd)
# print(table_names)

# counter1 = len(table_names)
# for key1 in range(counter1):
#     table = table_names[key1]
#     print("Table: ", table)

#     # result = _sqlite.select_all_tasks(dbd, table)                      # get all (shadow is too small for all data)
#     result = _sqlite.select_task_by_query(work_dir + _def.DB_SET_D, "SELECT ID, value FROM " + table)
#     print(result)
#     if (result != []):
#         # aws_shadow.shadowUpdate("rtd", table, result, True)              # result = list of dictionaries = json array (see shadowUpdateSingleDict) 
#         shadowUpdateSingleDict("rtd", table, result, True)


# for table_name in table_names:

#     if "sets" in table_name:
#         query = ("SELECT ID, value FROM " + table_name)
#         result = _sqlite.select_task_by_query(dbd, query)
#         print(result)
#         if (result != []):
#             shadowUpdateSingleDict("settings", table_name, result, False) 


def shadowUpdateSingleDict (db, table, list, init, idName="ID"):

    # 20220307
    # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! 
    # "Shadows support arrays, but treat them as normal values in that an update to an array replaces the whole array. It is not possible to update part of an array"
    # So I can't use standard export sqlite to json -> json array (looking for ":( json array") but as python dict -> object json (looking for ":) json object")
    # Send every ID to void to convert dict to string and so have json values as integer and not as string
    listSize = len(list)
    for listIdx in range(listSize):
        print(list[listIdx])
        mydict = list[listIdx]
        # id = mydict.get('ID')                             # get ID
        id = mydict.pop(idName)                               # get and delete ID from dict

        # remove None object from dict
        # for k, v in mydict.items():                       can't use because 'll change size
        for k, v in dict(mydict).items():
            if v == None:
                del mydict[k]
            if k == 'packetNum':                            # delete packetNum
                del mydict[k]

        # !! CAUTION: un messaggio shadow per ogni ID = $$$$$$$$$ !!
        if mydict:
            print(mydict)
            # aws_shadow.shadowUpdate(db, table, mydict, init, id)    # send every single ID 


# Trasformo la list python (array json) in dict python (object json) per migliore l'accessibilità chiave-valore del shadow (json) evitando quindi gli array json che in 
# AWS IOT shadow non possono essere modificati parzialmente ed inoltre non hanno funzioni build-in per un facile accesso ai valori
def listToDict(lst, idName="ID"):
    # Crea un dizionario che mappa ogni ID al dizionario pulito
    result = {}
    for item in lst:
        # Rimuove e ottiene l'ID
        item_id = item.pop(idName)

        # Rimuove chiavi non volute
        for k, v in dict(item).items():
            if v is None or k == 'packetNum':
                del item[k]

        if item:  # Se il dizionario non è vuoto
            result[item_id] = item

    return result


def shadowUpdateAlarms (shadowName):

    # !!eventualmente fare solo una chiamata a aws_shadow.shadowUpdateArray ... così da ridurre tx mqtt e quindi $$$$

    # !! Inoltre Attenzione: le regole AWS IOT CORE agiscono sul topic ../update/accepted quindi se la stessa shadow
    # !! viene aggiornata in momenti differenti, si possono avere le regole che resistuiscono un determinato valore,
    # !! filtrato nella regola stessa, vuoto. Quindi nelle regole AWS IOT CORE va verificata la presenza del key 
    # !! relativa al valore. Questo può anche essere risolto omettendo il delay tra gli aggiornamenti sulla stessa
    # !! shadow (time.sleep(1)) ma comunque non è garanzia assoluta, quindi occorre adottare una di queste:
    # !! - Aggiornare la stessa shadow in un colpo solo (così anche risparmio $$$)
    # !! - Gestire nella regola la verifica della presenza della chiave relativa al valore che si vuole ottenere

    print(f"Update shadow...{shadowName}")

    table_name = 'eventsMatrix'
    query = ('SELECT ID, ref, em_type FROM ' + table_name)
    events = _sqlite.select_task_by_query(DB_SET, query)

    # for item in events:
    #     # Rinomina la chiave "ref" in "ID" spostando il valore
    #     item['ID'] = item.pop('ref')

    table_name = 'alarms'
    query = ('SELECT ID, active, timeout FROM ' + table_name)
    alarms = _sqlite.select_task_by_query(DB_RTD, query)

    # for item in alarms:
    #     # Rinomina la chiave "name" in "ID" spostando il valore
    #     item['ID'] = item.pop('name')

    merged_list = []
    for item in events:
        # Trova il dizionario in alarms che ha lo stesso ID
        match = next((elem for elem in alarms if elem['ID'] == item['ID']), {})
        # Unisci i dizionari: le chiavi in match verranno aggiunte a quelle di item
        merged_item = {**item, **match}
        merged_list.append(merged_item)

    result = listToDict(merged_list)
    aws_shadow.shadowUpdateArray(shadowName, 'alarms', result, False)

    # time.sleep(1) 

    preAlarm = False
    alarm = False
    for item in merged_list:
        if _utility.to_int_safe(item['em_type']) != 0 and item['active'] == 1:
            preAlarm = True
            if alarm == True:
                break
        if _utility.to_int_safe(item['em_type']) != 0 and item['active'] == 2:
            alarm = True
            if preAlarm == True:
                break

    group_name = 'alarmsBFC'         # BFC = build for cloud
    alarmsGlob = [{'ID': 'preAlarms', 'value': preAlarm}, {'ID': 'alarms', 'value': alarm}]
    result = listToDict(alarmsGlob)
    aws_shadow.shadowUpdateArray(shadowName, group_name, result, False)




def shadowUpdateCycleInfo (shadowName):

    # !!eventualmente fare solo una chiamata a aws_shadow.shadowUpdateArray ... così da ridurre tx mqtt e quindi $$$$

    # !! Inoltre Attenzione: le regole AWS IOT CORE agiscono sul topic ../update/accepted quindi se la stessa shadow
    # !! viene aggiornata in momenti differenti, si possono avere le regole che resistuiscono un determinato valore,
    # !! filtrato nella regola stessa, vuoto. Quindi nelle regole AWS IOT CORE va verificata la presenza del key 
    # !! relativa al valore. Questo può anche essere risolto omettendo il delay tra gli aggiornamenti sulla stessa
    # !! shadow (time.sleep(1)) ma comunque non è garanzia assoluta, quindi occorre adottare una di queste:
    # !! - Aggiornare la stessa shadow in un colpo solo (così anche risparmio $$$)
    # !! - Gestire nella regola la verifica della presenza della chiave relativa al valore che si vuole ottenere
    payload = {}  # contiene tutti i dati da inviare alla shadow

    print(f"Update shadow...{shadowName}")

    table_name = 'rtd'
    query = ('SELECT * FROM ' + table_name)
    rtd = _sqlite.select_task_by_query(DB_RTD, query)
    # result = listToDict(rtd)
    # aws_shadow.shadowUpdateArray(shadowName, table_name, result, False)
    payload[table_name] = listToDict(rtd)

    # time.sleep(1) 

    table_name = 'sets_work'
    query = ('SELECT ID, value, description FROM ' + table_name)
    query = ('SELECT ID, value FROM ' + table_name)
    sets_work = _sqlite.select_task_by_query(DB_SET, query)
    # result = listToDict(sets_work)
    # aws_shadow.shadowUpdateArray(shadowName, table_name, result, False)
    payload[table_name] = listToDict(sets_work)

    # time.sleep(1) 

    group_name = 'PhasesInfoBFC'         # BFC = build for cloud
    table_name = 'CurPrg'
    query = ('SELECT COUNT(*) FROM ' + table_name)
    result = _sqlite.select_task_by_query(DB_PRG, query)
    phases_num = [{'ID': 'PhasesNum', 'value': result[0]['COUNT(*)']}]
    # result = listToDict(phases_num)
    # aws_shadow.shadowUpdateArray(shadowName, group_name, result, False)
    payload[group_name] = listToDict(phases_num)
    
    
    table_name = 'io'
    query = ('SELECT name, val FROM ' + table_name)
    io = _sqlite.select_task_by_query(DB_RTD, query)
    # result = listToDict(io)
    # aws_shadow.shadowUpdateArray(shadowName, table_name, result, False)
    payload[table_name] = listToDict(io, 'name')
    
    
    table_name = 'sets_cOptions'
    query = ('SELECT ID, value FROM ' + table_name + ' WHERE ID IN ("tempUnit","humiUnit")')
    sets_cOptions = _sqlite.select_task_by_query(DB_SET, query)
    # result = listToDict(sets_cOptions)
    # aws_shadow.shadowUpdateArray(shadowName, table_name, result, False)
    payload[table_name] = listToDict(sets_cOptions)
    
    # Una singola chiamata con tutto il payload
    aws_shadow.shadowUpdateArray(shadowName, None, payload, False)

def shadowUpdateMainSets (shadowName):

    payload = {}  # contiene tutti i dati da inviare alla shadow

    print(f"Update shadow...{shadowName}")

    table_name = 'sets_manualMode'
    query = ('SELECT ID, value, minValue, maxValue FROM ' + table_name)
    sets_manualMode = _sqlite.select_task_by_query(DB_SET, query)
    payload[table_name] = listToDict(sets_manualMode)
    
    # Una singola chiamata con tutto il payload
    aws_shadow.shadowUpdateArray(shadowName, None, payload, False)


# def shadowUpdateFromQuery (shadowName, query, db):
def shadowUpdateFromQuery (table_name, id_name, query, db):
    
    # table_name = _sqlite.get_tabel_name_from_query(query)
    shadowName = table_name
    
    print(f"Update shadow...{shadowName}")

    result = _sqlite.select_task_by_query(db, query)
    result = listToDict(result, id_name)
    aws_shadow.shadowUpdateArray(shadowName, table_name, result, False)
    

def shadowUpdateSync ():
# if __name__ == '__main__': 
#     query = ("SELECT ref, em_type FROM eventsMatrix")
#     result = _sqlite.select_task_by_query(_def.work_dir + _def.DB_SET_D, query)
#     aws_shadow.shadowUpdate("alarm", "alarm", result, True)
#     print(result)

    # table_name = 'sets_cOptions'
    # query = ('SELECT ID, value FROM ' + table_name)
    # result = _sqlite.select_task_by_query(_def.work_dir + _def.DB_SET_D, query)
    # aws_shadow.shadowUpdateArray('settingsArray', table_name, result, False)
    # shadowUpdateSingleDict("settings", table_name, result, False)

    shadowUpdateAlarms('alarms')
    time.sleep(1)  
    shadowUpdateCycleInfo('cycleInfo')
    time.sleep(1)  
    shadowUpdateMainSets('mainSets')
    # shadowUpdateFromQuery('io', 'name', 'SELECT name, val FROM io', DB_RTD)

    # print(alarms_dict)