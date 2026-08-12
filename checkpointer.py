import os
from dotenv import load_dotenv
from langgraph.checkpoint.postgres import PostgresSaver
import psycopg
load_dotenv()

DATABASE_URL  = os.getenv("DATABASE_URL")

conn = psycopg.connect(DATABASE_URL, autocommit=True)
checkpointer = PostgresSaver(conn)
checkpointer.setup()
def get_checkpointer():
  return checkpointer
