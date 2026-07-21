import mysql.connector
import os
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash

load_dotenv()

def get_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password=os.getenv('DB_PASSWORD'),
        database="medease_db"
    )

def register_user(email, password):
    """
    Registers a new user by checking if the email exists, 
    hashing the password, and inserting it into the database.
    Returns (True, "Success message") or (False, "Error message").
    """
    email_clean = email.strip().lower()
    if not email_clean or not password:
        return False, "Email and password cannot be empty."

    password_hash = generate_password_hash(password)

    conn = None
    cursor = None
    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)

        # Check if user already exists
        cursor.execute("SELECT id FROM users WHERE email = %s", (email_clean,))
        if cursor.fetchone():
            return False, "An account with this email address already exists."

        # Insert new user
        cursor.execute(
            "INSERT INTO users (email, password_hash) VALUES (%s, %s)",
            (email_clean, password_hash)
        )
        conn.commit()
        return True, "Registration successful!"

    except Exception as e:
        print(f"DATABASE ERROR during registration: {e}")
        return False, "An error occurred while creating your account. Please try again."
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def authenticate_user(email, password):
    """
    Checks user credentials.
    Returns (True, user_dict) or (False, "Error message").
    """
    email_clean = email.strip().lower()
    if not email_clean or not password:
        return False, "Email and password cannot be empty."

    conn = None
    cursor = None
    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)

        # Retrieve user details
        cursor.execute(
            "SELECT id, email, password_hash FROM users WHERE email = %s", 
            (email_clean,)
        )
        user = cursor.fetchone()
        
        if not user:
            return False, "Invalid email address or password."

        # Verify hashed password
        if check_password_hash(user['password_hash'], password):
            return True, {
                'id': user['id'],
                'email': user['email']
            }
        else:
            return False, "Invalid email address or password."

    except Exception as e:
        print(f"DATABASE ERROR during authentication: {e}")
        return False, "An error occurred during login. Please try again."
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
