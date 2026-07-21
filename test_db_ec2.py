import os
from dotenv import load_dotenv
import mysql.connector

load_dotenv()
try:
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password=os.getenv('DB_PASSWORD'),
        database='medease_db'
    )
    print("SUCCESS CONNECT")
    cursor = conn.cursor()
    cursor.execute("SELECT id, email FROM users")
    users = cursor.fetchall()
    print(f"USERS FOUND: {users}")
except Exception as e:
    print(f"DATABASE ERROR: {e}")
