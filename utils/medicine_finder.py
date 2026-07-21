import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()

def get_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password=os.getenv('DB_PASSWORD'),
        database="medease_db"
    )

def find_substitute(brand_name):
    """Search medicines table for generic substitutes"""
    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT 
                brand_name,
                generic_name,
                composition,
                price_brand,
                price_generic,
                ROUND((price_brand - price_generic), 2) AS savings,
                ROUND((price_brand - price_generic) / price_brand * 100, 0) AS savings_pct
            FROM medicines
            WHERE LOWER(brand_name) LIKE %s
            ORDER BY savings_pct DESC
        """, (f'%{brand_name.lower()}%',))

        results = cursor.fetchall()
        cursor.close()
        conn.close()
        return results

    except Exception as e:
        print(f"DATABASE ERROR: {e}")
        return None