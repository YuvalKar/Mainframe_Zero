import os
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Global variable to hold the model in memory so we don't load it multiple times
_local_model = None

def get_db_connection():
    """Establish and return a connection to the PostgreSQL database."""
    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST", "localhost"),
            port=os.getenv("DB_PORT", "5432"),
            dbname=os.getenv("DB_NAME", "postgres"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", "")
        )
        return conn
    except Exception as e:
        print(f"[Memory DB Error: Failed to connect to database - {e}]")
        return None

def get_local_model():
    """Load and return the local BAAI/bge-m3 model using Lazy Loading."""
    global _local_model
    if _local_model is None:
        print("Loading BAAI/bge-m3 model (this might take a bit longer to download the first time)...")
        # We import it HERE, only when actually requested, to save startup time!
        from sentence_transformers import SentenceTransformer
        _local_model = SentenceTransformer('BAAI/bge-m3')
    return _local_model


# TODO: Implement Database Connection Pooling
# Currently, every DB operation opens and closes a new connection. This is resource-heavy 
# and will introduce latency, especially during the recursive queries used for LOD context assembly.
# Refactor get_db_connection() to utilize a connection pool (e.g., psycopg2.pool.SimpleConnectionPool 
# or ThreadedConnectionPool) to maintain and reuse active connections, significantly improving performance.