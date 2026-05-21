#!/usr/bin/env python3
import argparse
import sys
import json

# from app.aws_connect import connect
# import app.aws_connect as aws
from app import aws_connect
import time
from app import shadow_man

##############################################################
# Comandi per compilare 
# cd cloud
# pyinstaller --onefile --clean --paths=/home/lg58/LDC-100 de01cloud.py
##############################################################
info_file = "version.json"
#================================================================================

def get_version():
    try:
        with open(info_file, "r", encoding="utf-8") as file:
            data = json.load(file)
            versione = data.get("version")
    except FileNotFoundError:
        print(f"Errore: Il file '{info_file}' non esiste.")
    except json.JSONDecodeError:
        print("Errore: Il file non contiene un formato JSON valido.")
    return versione
#================================================================================

if __name__ == '__main__': 
    parser = argparse.ArgumentParser(description='LDC-100 Cloud Software by LOGICA H&S Srl')
    args, unknown = parser.parse_known_args()  # ignora argomenti sconosciuti
    SW_VERSION = get_version
    
    print("")
    print('-------------------------------------------------------')
    print("LDC-100 CLOUD SOFTWARE by LOGICA H&S Srl. Version: ", SW_VERSION)
    print('-------------------------------------------------------')
    print("")

    time.sleep(1)
    # Configure your AWS IoT Thing details
    aws_connect.connect()

    # getShadowSize("ML00010", "settings")

    while True:

        # esempio cosa mandare su Client di test MQTT awsSqlQuery
        
        # Nome argomento:
        # devices/ML00010/sql/query

        # Payload del messaggio
        # {
        # "message": "SQL UPDATE sets_cOptions SET value = 10 WHERE ID = 'co_contrast' @settings"
        # }

        # {
        # "message": "SQL INSERT OR REPLACE INTO changes (ID, modified, param) VALUES ('sets_cOptions', 1, 'co_contrast') @settings"
        # }

        # {
        # "message": "SQL SELECT ID, value FROM sets_cOptions @settings"
        # }
        
        try:

            while True:
                try:
                    # print("attendo query")
                    shadow_man.shadowUpdateSync()
                    time.sleep(15)

                    # query = ("SELECT * FROM sets_cOptions")
                    # result = _sqlite.select_task_by_query(dbd, query)
                    # print(result)
                    # if (result != []):
                    #     shadowUpdateSingleDict("settings", "sets_cOptions", result, False) 
                except Exception as error:
                    print("An error occurred:", error)
                    aws_connect.exit(error)
                    time.sleep(5)   
                    aws_connect.connect() 
                    # break

        except Exception as error:
            print("An error occurred:", error) 
            aws_connect.exit(error)   
        except OSError: 
            print("An OSError occurred")
        # except:
        #     print("An except occurred")       
        finally:
            aws_connect.exit("exit")

            time.sleep(5)
            print('===================================================================')
            print ("Application closed")
            sys.exit()