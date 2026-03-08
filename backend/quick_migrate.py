import pymysql
try:
    conn=pymysql.connect(host='localhost', user='root', password='newpassword', database='federated_healthcare')
    cursor=conn.cursor()
    cursor.execute('ALTER TABLE model_weights ADD COLUMN local_mae FLOAT NULL')
except: pass
try: cursor.execute('ALTER TABLE model_weights ADD COLUMN local_mse FLOAT NULL')
except: pass
try: cursor.execute('ALTER TABLE model_weights ADD COLUMN local_adjusted_r2 FLOAT NULL')
except: pass
try: cursor.execute('ALTER TABLE model_weights ADD COLUMN local_smape FLOAT NULL')
except: pass
try: cursor.execute('ALTER TABLE model_weights ADD COLUMN local_wape FLOAT NULL')
except: pass
try: cursor.execute('ALTER TABLE model_weights ADD COLUMN local_mase FLOAT NULL')
except: pass
try: cursor.execute('ALTER TABLE model_weights ADD COLUMN local_rmsle FLOAT NULL')
except: pass
conn.commit()
cursor.execute('SHOW COLUMNS FROM model_weights')
cols=[row[0] for row in cursor.fetchall()]
missing=[c for c in ['local_mae','local_mse','local_adjusted_r2','local_smape','local_wape','local_mase','local_rmsle'] if c not in cols]
print('OK' if not missing else f"Missing: {missing}")
conn.close()
