import os
from dotenv import load_dotenv

# 👉 CHANGED: Importing the ASYNC pool and ASYNC saver
from psycopg_pool import AsyncConnectionPool
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

load_dotenv()

async def get_async_checkpointer():
    """
    Initializes an asynchronous PostgreSQL checkpointer for LangGraph.
    Returns both the checkpointer and the pool so we can safely close the pool later.
    """
    db_url = os.getenv("DATABASE_URL")
    
    if not db_url:
        raise ValueError("DATABASE_URL is missing from your .env file!")

    print("🗄️ Connecting to Neon PostgreSQL (Async)...")
    
    # 1. Create the async connection pool
    pool = AsyncConnectionPool(conninfo=db_url)
    
    # 2. Wrap it in the AsyncPostgresSaver
    checkpointer = AsyncPostgresSaver(pool)
    
    # 3. Setup the database tables asynchronously (creates them if they don't exist)
    await checkpointer.setup()
    
    return checkpointer, pool