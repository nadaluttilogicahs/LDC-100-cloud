#import boto3

# SQLite connection
# conn = sqlite3.connect(r"/home/pi/local.db")
# cursor = conn.cursor()
# cursor.execute("SELECT ID, description FROM sets_cOptions")

# dynamodb = boto3.resource('dynamodb')
# table = dynamodb.Table('cloud')

# # Insert data
# for row in cursor.fetchall():
#     table.put_item(Item={
#         'PrimaryKey': row[0],
#         'OtherAttribute': row[1]
#     })
# conn.close()

# # Funzione per estrarre i dati da una tabella SQLite
# def fetch_data_from_sqlite(table_name):
#     conn = sqlite3.connect(dbd)  # Connessione al database SQLite
#     cursor = conn.cursor()
    
#     # Esegui una query per ottenere tutti i dati della tabella
#     cursor.execute(f"SELECT ID, value FROM {table_name}")
#     data = cursor.fetchall()
    
#     conn.close()
    
#     return data


# # Funzione per inserire i dati in DynamoDB
# def insert_data_into_dynamodb(table_name, sqlite_data):
#     dynamodb = boto3.resource('dynamodb')
#     table = dynamodb.Table('ML00001_set')  # Nome della tabella DynamoDB
    
#     for record in sqlite_data:
#         # Creiamo un dizionario che rappresenta il record da inserire in DynamoDB
#         item = {
#             'Table': table_name,  # Nome della tabella come chiave di partizione
#             'Id': str(record[0]),  # ID del record come chiave di ordinamento
#         }

#         # Aggiungi le altre colonne come attributi
#         for i, col in enumerate(record[1:], start=1):  # salta la prima colonna (ID)
#             item[f'Value{i}'] = col
        
#         # Inserisci l'elemento in DynamoDB
#         table.put_item(Item=item)
#         print(f'Inserito record con ID: {record[0]} nella tabella {table_name}')



# table_names = _sqlite.select_tables_name(dbd)
# print(table_names)

# # for table_name in table_names:

# #     if "sets" in table_name:
# #         # Estrai i dati dalla tabella SQLite
# #         sqlite_data = fetch_data_from_sqlite(table_name)

# #         # Inserisci i dati in DynamoDB
# #         insert_data_into_dynamodb(table_name, sqlite_data)