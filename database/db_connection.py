import os
from psycopg2 import pool
from dotenv import load_dotenv
from core_utils.hud_streamer import send_hud_error, send_hud_text


# Load environment variables
load_dotenv()

# Global variables to hold our singletons in memory
_local_model = None
_connection_pool = None

def _init_pool():
    """Initialize the connection pool if it doesn't exist."""
    global _connection_pool
    if _connection_pool is None:
        try:
            # Create a pool with a minimum of 1 and maximum of 10 connections
            _connection_pool = pool.SimpleConnectionPool(
                1, 10,
                host=os.getenv("DB_HOST", "localhost"),
                port=os.getenv("DB_PORT", "5432"),
                dbname=os.getenv("DB_NAME", "postgres"),
                user=os.getenv("DB_USER", "postgres"),
                password=os.getenv("DB_PASSWORD", "")
            )
        except Exception as e:
            send_hud_error("DB_CONNECTION", f"Failed to initialize connection pool - {e}", code=2802552)
            print(f"[Memory DB Error: Failed to initialize connection pool - {e}]")

def get_db_connection():
    """Get an active connection from the pool."""
    _init_pool()
    if _connection_pool:
        try:
            return _connection_pool.getconn()
        except Exception as e:
            send_hud_error("DB_CONNECTION", f"Failed to get connection from pool - {e}", code=3802552)
            print(f"[Memory DB Error: Failed to get connection from pool - {e}]")
    return None

def release_db_connection(conn):
    """Release the connection back to the pool for reuse."""
    global _connection_pool
    if _connection_pool and conn:
        try:
            _connection_pool.putconn(conn)
        except Exception as e:
            send_hud_error("DB_CONNECTION", f"Failed to release connection back to pool - {e}", code=4802552)
            print(f"[Memory DB Error: Failed to release connection - {e}]")

def get_local_model():
    """Load and return the local BAAI/bge-m3 model using Lazy Loading."""
    global _local_model
    if _local_model is None:
        send_hud_text("LOCAL_MODEL", "Loading local model (this might take a bit longer the first time)", level="warning")
        print("Loading BAAI/bge-m3 model (this might take a bit longer to download the first time)...")
        from sentence_transformers import SentenceTransformer
        _local_model = SentenceTransformer('BAAI/bge-m3')
    return _local_model