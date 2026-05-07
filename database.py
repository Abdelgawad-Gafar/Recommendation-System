import os
import logging
import chromadb
import pyodbc
from dotenv import load_dotenv

load_dotenv()

# إعداد الـ Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler("app.log"), logging.StreamHandler()]
)
logger = logging.getLogger("AlluvoDB")

# 1. ChromaDB
CHROMA_PATH = os.getenv("CHROMA_PATH", "./alluvo_vector_db")
chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)
reels_collection = chroma_client.get_or_create_collection(name="alluvo_reels")

# 2. SQL Server
def get_sql_conn():
    driver = os.getenv('SQL_DRIVER', '{SQL Server}')
    server = os.getenv('SQL_SERVER')
    database = os.getenv('SQL_DATABASE')
    uid = os.getenv('SQL_UID')
    pwd = os.getenv('SQL_PWD')

    if not server or not database:
        logger.error("Database configuration incomplete: SQL_SERVER or SQL_DATABASE missing")
        raise RuntimeError("Database configuration incomplete")

    conn_str = f"DRIVER={driver};SERVER={server};DATABASE={database};UID={uid};PWD={pwd}"
    try:
        return pyodbc.connect(conn_str, timeout=5)
    except Exception as e:
        logger.exception("Failed to connect to SQL Server")
        raise