import json
import os
import subprocess

def expand_placeholders(value, parameters):
    """
    Sostituisce i placeholder del tipo ${aws:iot:parameter:<key>}
    con i valori effettivi presi da 'parameters'.
    Esempio: se value = "Scarica da ${aws:iot:parameter:downloadUrl}",
    e parameters["downloadUrl"] = "https://example.com/...",
    otterrai "Scarica da https://example.com/...".
    
    Se 'value' è una lista, la funzione itera su ciascun elemento.
    Se 'value' è un dict, sostituisce in modo ricorsivo i valori stringa.
    """
    if isinstance(value, str):
        # Per semplicità, sostituiamo TUTTE le occorrenze
        # del pattern ${aws:iot:parameter:<chiave>}
        # con parameters[<chiave>] se esiste.
        # In un caso reale potresti usare una regex o fare controlli più raffinati.
        for key, val in parameters.items():
            placeholder = f'${{aws:iot:parameter:{key}}}'
            value = value.replace(placeholder, str(val))
        return value
    
    elif isinstance(value, list):
        return [expand_placeholders(item, parameters) for item in value]
    
    elif isinstance(value, dict):
        return {k: expand_placeholders(v, parameters) for k, v in value.items()}
    
    else:
        return value

def process_job_document(job_document_str, job_parameters):
    """
    job_document_str: stringa JSON del job document
    job_parameters: dict con le variabili da sostituire
    """
    try:
        doc = json.loads(job_document_str)
    except json.JSONDecodeError as e:
        print(f"Errore nel parsing del JSON: {e}")
        return

    steps = doc.get("steps", [])
    if not steps:
        print("Nessuno step trovato nel job document.")
        return
    
    for step in steps:
        action = step.get("action", {})
        action_type = action.get("type")
        if action_type == "runHandler":
            print(f"[DEBUG] Eseguo lo step runHandler: {action.get('name', '(no name)')}")
            
            # Espandiamo i placeholder nell'intero blocco 'action'
            # in modo da avere già i valori reali.
            action_expanded = expand_placeholders(action, job_parameters)
            
            handler_path = action_expanded.get("input", {}).get("handler")
            path_to_handler = action_expanded.get("input", {}).get("path")
            args = action_expanded.get("input", {}).get("args", [])
            run_as_user = action_expanded.get("runAsUser")
            
            # Se esiste un path specifico in cui si trova lo script, uniamo i percorsi
            if path_to_handler:
                handler_full_path = os.path.join(path_to_handler, handler_path)
            else:
                handler_full_path = handler_path
            
            print(f" - Script: {handler_full_path}")
            print(f" - Argomenti: {args}")
            print(f" - Eseguito come utente: {run_as_user if run_as_user else 'corrente'}")

            # Prepara il comando per subprocess
            # Esempio semplificato: se 'runAsUser' è diverso dall'utente corrente,
            # potresti lanciare 'sudo -u runAsUser ...'
            # Ma qui faremo solo un esempio "banale".
            
            cmd = [handler_full_path] + args
            
            if run_as_user and run_as_user != os.getlogin():
                cmd = ["sudo", "-u", run_as_user] + cmd
            
            print(f"[DEBUG] Comando completo da eseguire: {cmd}")
            
            # Esegui il comando (in produzione valuta try/except, logging, ecc.)
            try:
                result = subprocess.run(cmd, check=True, capture_output=True, text=True)
                print("[INFO] Script eseguito con successo.")
                print("[INFO] Output:", result.stdout)
            except subprocess.CalledProcessError as e:
                print(f"[ERRORE] Script terminato con codice {e.returncode}")
                print("stdout:", e.stdout)
                print("stderr:", e.stderr)
        else:
            print(f"[DEBUG] Step con type={action_type} non supportato in questo esempio.")

def main():
    # Esempio di job document (stringa):
    job_document_str = r'''
    {
      "version": "1.0",
      "steps": [
        {
          "action": {
            "name": "Download-File",
            "type": "runHandler",
            "input": {
              "handler": "download-file.sh",
              "args": [
                "${aws:iot:parameter:downloadUrl}",
                "${aws:iot:parameter:filePath}"
              ],
              "path": "${aws:iot:parameter:pathToHandler}"
            },
            "runAsUser": "${aws:iot:parameter:runAsUser}"
          }
        }
      ]
    }
    '''
    
    # Parametri reali da sostituire
    job_parameters = {
      "downloadUrl": "https://example.com/myfile.bin",
      "filePath": "/tmp/myfile.bin",
      "pathToHandler": "/home/pi/scripts",
      "runAsUser": "pi"
    }

    # Chiama la funzione che processa ed esegue gli step
    process_job_document(job_document_str, job_parameters)

if __name__ == "__main__":
    main()
