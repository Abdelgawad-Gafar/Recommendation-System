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
    conn_str = f"DRIVER={os.getenv('SQL_DRIVER', '{SQL Server}')};SERVER={os.getenv('SQL_SERVER', 'YOUR_SERVER')};DATABASE={os.getenv('SQL_DATABASE', 'AlluvoDB')};UID={os.getenv('SQL_UID', 'user')};PWD={os.getenv('SQL_PWD', 'pass')}"
    return pyodbc.connect(conn_str)