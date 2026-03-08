import pymysql
import time

try:
    print("Connecting...", flush=True)
    conn = pymysql.connect(host='localhost', user='root', password='newpassword', database='federated_healthcare', connect_timeout=5)
    cursor = conn.cursor()
    
    print("Adding columns...", flush=True)
    
    stmts = [
        "ALTER TABLE model_weights ADD COLUMN local_mse FLOAT",
        "ALTER TABLE model_weights ADD COLUMN local_adjusted_r2 FLOAT",
        "ALTER TABLE model_weights ADD COLUMN local_smape FLOAT",
        "ALTER TABLE model_weights ADD COLUMN local_wape FLOAT",
        "ALTER TABLE model_weights ADD COLUMN local_mase FLOAT",
        "ALTER TABLE model_weights ADD COLUMN local_rmsle FLOAT",
    ]
    
    for stmt in stmts:
        try:
            cursor.execute(stmt)
            print(f"OK: {stmt}", flush=True)
        except pymysql.err.OperationalError as e:
            if "Duplicate column" in str(e):
                print(f"SKIP: Column exists ({stmt})", flush=True)
            else:
                print(f"ERR: {e}", flush=True)
    
    conn.commit()
    print("Committed", flush=True)
    conn.close()
    print("DONE", flush=True)
    
except Exception as e:
    print(f"Exception: {e}", flush=True)
