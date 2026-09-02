from sqlalchemy import create_engine
import pandas as pd

try:
    engine = create_engine('mysql+pymysql://root:@127.0.0.1:3306/plcdata')
    df = pd.read_sql('SHOW TRIGGERS;', engine)
    print(df.to_string())
except Exception as e:
    print(f"Error: {e}")
