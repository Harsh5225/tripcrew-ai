import os
import psycopg
from dotenv import load_dotenv

load_dotenv()

conn_string = os.getenv("DATABASE_URL")

if not conn_string:
    print("❌ DATABASE_URL not found — check your .env file")
else:
    try:
        with psycopg.connect(conn_string) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT version();")
                print("✅ Connected successfully!")
                print(cur.fetchone())
    except Exception as e:
        print("❌ Connection failed:", e)