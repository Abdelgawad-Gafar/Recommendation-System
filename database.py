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
    driver = os.getenv('SQL_DRIVER', '{ODBC Driver 18 for SQL Server}')
    server = os.getenv('SQL_SERVER')
    database = os.getenv('SQL_DATABASE')
    uid = os.getenv('SQL_USERNAME')
    pwd = os.getenv('SQL_PASSWORD')

    logger.info(f"SQL_SERVER={server}")
    logger.info(f"SQL_DATABASE={database}")
    logger.info(f"SQL_USERNAME={uid}")

    if not server or not database:
        logger.error("Database configuration incomplete: SQL_SERVER or SQL_DATABASE missing")
        raise RuntimeError("Database configuration incomplete")

    conn_str = (
        f"DRIVER={driver};"
        f"SERVER={server};"
        f"DATABASE={database};"
        f"UID={uid};"
        f"PWD={pwd};"
        "Encrypt=no;"
        "TrustServerCertificate=yes;"
    )

    try:
        return pyodbc.connect(conn_str, timeout=5)
    except Exception:
        logger.exception("Failed to connect to SQL Server")
        raise
