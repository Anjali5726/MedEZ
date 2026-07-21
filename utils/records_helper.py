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

def create_folder(user_id, name):
    """Create a new folder for the user"""
    name_clean = name.strip()
    if not name_clean:
        return False, "Folder name cannot be empty."
        
    conn = None
    cursor = None
    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        
        # Check duplicate folder name for this user
        cursor.execute(
            "SELECT id FROM folders WHERE user_id = %s AND name = %s", 
            (user_id, name_clean)
        )
        if cursor.fetchone():
            return False, f"A folder named '{name_clean}' already exists."
            
        cursor.execute(
            "INSERT INTO folders (user_id, name) VALUES (%s, %s)",
            (user_id, name_clean)
        )
        conn.commit()
        return True, "Folder created successfully!"
    except Exception as e:
        print(f"DATABASE ERROR in create_folder: {e}")
        return False, "An error occurred while creating the folder."
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

def get_folders(user_id):
    """Retrieve all folders created by a user"""
    conn = None
    cursor = None
    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT id, name, created_at FROM folders WHERE user_id = %s ORDER BY name ASC",
            (user_id,)
        )
        return cursor.fetchall()
    except Exception as e:
        print(f"DATABASE ERROR in get_folders: {e}")
        return []
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

def save_report(user_id, folder_id, report_type, title, original_text, original_pdf_path, analysis_result):
    """Save an AI analysis report to the database"""
    title_clean = title.strip()
    if not title_clean:
        title_clean = "Unnamed Report"
        
    # Convert empty/zero folder_id to None
    f_id = None
    if folder_id:
        try:
            f_id = int(folder_id)
        except ValueError:
            pass
            
    conn = None
    cursor = None
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO saved_reports (user_id, folder_id, report_type, title, original_text, original_pdf_path, analysis_result)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (user_id, f_id, report_type, title_clean, original_text, original_pdf_path, analysis_result))
        conn.commit()
        return True, "Report saved successfully!"
    except Exception as e:
        print(f"DATABASE ERROR in save_report: {e}")
        return False, "An error occurred while saving the report."
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

def get_reports(user_id, folder_id=None):
    """Get reports belonging to a user. Optionally filter by folder_id."""
    conn = None
    cursor = None
    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        
        if folder_id is not None:
            # Get folder reports
            cursor.execute("""
                SELECT id, folder_id, report_type, title, original_pdf_path, created_at 
                FROM saved_reports 
                WHERE user_id = %s AND folder_id = %s 
                ORDER BY created_at DESC
            """, (user_id, folder_id))
        else:
            # Get all reports (along with folder name if applicable)
            cursor.execute("""
                SELECT r.id, r.folder_id, r.report_type, r.title, r.original_pdf_path, r.created_at, f.name AS folder_name
                FROM saved_reports r
                LEFT JOIN folders f ON r.folder_id = f.id
                WHERE r.user_id = %s
                ORDER BY r.created_at DESC
            """, (user_id,))
            
        return cursor.fetchall()
    except Exception as e:
        print(f"DATABASE ERROR in get_reports: {e}")
        return []
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

def get_report_details(user_id, report_id):
    """Retrieve details of a specific saved report"""
    conn = None
    cursor = None
    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT r.id, r.folder_id, r.report_type, r.title, r.original_text, r.original_pdf_path, r.analysis_result, r.created_at, f.name AS folder_name
            FROM saved_reports r
            LEFT JOIN folders f ON r.folder_id = f.id
            WHERE r.user_id = %s AND r.id = %s
        """, (user_id, report_id))
        return cursor.fetchone()
    except Exception as e:
        print(f"DATABASE ERROR in get_report_details: {e}")
        return None
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

def delete_report(user_id, report_id):
    """Delete a specific report and clean up any local PDF uploads"""
    conn = None
    cursor = None
    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        
        # Get PDF path to delete it from disk
        cursor.execute(
            "SELECT original_pdf_path FROM saved_reports WHERE user_id = %s AND id = %s",
            (user_id, report_id)
        )
        report = cursor.fetchone()
        
        if not report:
            return False, "Report not found."
            
        # Delete from database
        cursor.execute(
            "DELETE FROM saved_reports WHERE user_id = %s AND id = %s",
            (user_id, report_id)
        )
        conn.commit()
        
        # Clean up local PDF or S3 object
        pdf_path = report.get('original_pdf_path')
        if pdf_path:
            if os.path.exists(pdf_path):
                try:
                    os.remove(pdf_path)
                except Exception as pe:
                    print(f"Error removing PDF file {pdf_path}: {pe}")
            else:
                # Try S3 delete
                from utils.s3_helper import delete_file_from_s3, is_s3_configured
                if is_s3_configured():
                    delete_file_from_s3(pdf_path)
                
        return True, "Report deleted successfully."
    except Exception as e:
        print(f"DATABASE ERROR in delete_report: {e}")
        return False, "An error occurred while deleting the report."
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

def delete_folder(user_id, folder_id):
    """Delete a folder. Note: linked reports will have folder_id set to NULL due to ON DELETE SET NULL constraint."""
    conn = None
    cursor = None
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM folders WHERE user_id = %s AND id = %s",
            (user_id, folder_id)
        )
        conn.commit()
        return True, "Folder deleted successfully."
    except Exception as e:
        print(f"DATABASE ERROR in delete_folder: {e}")
        return False, "An error occurred while deleting the folder."
    finally:
        if cursor: cursor.close()
        if conn: conn.close()
