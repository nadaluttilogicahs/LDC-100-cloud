import socket
import json

from ldc_common._paths import PATHS
from ldc_common import _sqlite


SOCKET_HOST = "127.0.0.1"
SOCKET_PORT = 2000
SOCKET_TIMEOUT_S = 3.0

USE_SOCKET = True  # flag globale, o lo passi come parametro

def query_db (db_tag: str, query: str, use_socket: bool = USE_SOCKET):
    """
    Esegue una SELECT su db_tag.
    Se use_socket=True passa per il socket server (come fa la GUI),
    altrimenti accede direttamente a SQLite.
    
    db_tag: 'settings', 'rtd', 'prg', 'language', o nome file archivio
    """
    if use_socket:
        msg = f"SQL {query} @{db_tag}\n"
        try:
            with socket.create_connection((SOCKET_HOST, SOCKET_PORT), timeout=SOCKET_TIMEOUT_S) as s:
                s.settimeout(SOCKET_TIMEOUT_S)
                s.sendall(msg.encode("utf-8"))
                
                chunks = []
                while True:
                    data = s.recv(4096)
                    if not data:
                        break
                    chunks.append(data)
                    if len(data) < 4096:
                        break
                
                raw = b''.join(chunks).decode("utf-8", errors="replace")
                try:
                    return json.loads(raw)
                except json.JSONDecodeError:
                    return raw  # 'DONE' o stringa errore
        except Exception as e:
            print(f"[query_db] socket error: {e}")
            return []
    else:
        # Uguale a socket (de01socket)
        db = _db_path(db_tag)
        if db == 'NONE':
            return 'no existing DB'
        q = query.upper()
        if 'SELECT' in q and not any(k in q for k in ('UPDATE', 'INSERT', 'CREATE')):
            return _sqlite.select_task_by_query(db, query)
        elif any(k in q for k in ('UPDATE', 'INSERT', 'REPLACE')):
            result = _sqlite.update_task_by_query(db, query)
            return result if result != [] else 'DONE'
        else:
            result = _sqlite.update_task_by_query(db, query)
            return result if result != [] else 'DONE'


def _db_path(db_tag: str) -> str:
    """Mappa db_tag → path SQLite, speculare al socket server."""
    if db_tag == 'settings':
        return PATHS.db_set
    elif db_tag == 'rtd':
        return PATHS.db_rtd
    elif db_tag == 'prg':
        return PATHS.db_prg
    elif db_tag == 'language':
        return PATHS.db_lan
    else:
        return PATHS.db_arc_dir + db_tag + '.db'