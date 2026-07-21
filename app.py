from flask import Flask, render_template, request, redirect, jsonify, session
from dotenv import load_dotenv
import os
from werkzeug.utils import secure_filename

load_dotenv()

from utils.pdf_reader import extract_text_from_pdf
from utils.ai_helper import translate_discharge, explain_medical_report

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024
app.secret_key = os.getenv('SECRET_KEY', 'medease_secure_development_key_2026')

# ── ROUTES ──────────────────────────────────────────

@app.route('/')
def index():
    if session.get('user') or session.get('guest'):
        return redirect('/dashboard')
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if not session.get('user') and not session.get('guest'):
        return redirect('/')
    return render_template('home.html')

@app.route('/discharge', methods=['GET', 'POST'])
def discharge():
    analysis_result = None
    error_message = None
    query_text = ""
    folders = []
    save_success = False

    # Get folders if user is logged in
    if session.get('user'):
        from utils.records_helper import get_folders
        folders = get_folders(session['user']['id'])

    if request.method == 'POST':
        query_text = request.form.get('query', '')
        saved_pdf_path = None

        if 'pdf_file' in request.files and request.files['pdf_file'].filename != '':
            file = request.files['pdf_file']

            if not file.filename.endswith('.pdf'):
                error_message = "Please upload a PDF file only."
            else:
                filename = secure_filename(file.filename)
                if not filename:
                    filename = "upload.pdf"
                
                # Check if they checked should_save
                should_save = request.form.get('should_save') == 'yes' and session.get('user')
                
                if should_save:
                    # Save to permanent uploads directory
                    import time
                    user_id = session['user']['id']
                    timestamp = int(time.time())
                    stored_filename = f"user_{user_id}_{timestamp}_{filename}"
                    
                    # Ensure uploads dir exists
                    uploads_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'uploads')
                    if not os.path.exists(uploads_dir):
                        os.makedirs(uploads_dir)
                        
                    local_dest = os.path.join(uploads_dir, stored_filename)
                    file.save(local_dest)
                    
                    # Extract text BEFORE uploading to S3 and deleting local file!
                    text = extract_text_from_pdf(local_dest)
                    if not text:
                        error_message = "Could not read this PDF. It may be a scanned image."
                        try:
                            os.remove(local_dest)
                        except Exception:
                            pass
                    else:
                        query_text += "\n" + text
                        
                        # Try S3 upload if configured
                        from utils.s3_helper import upload_file_to_s3, is_s3_configured
                        if is_s3_configured():
                            s3_key = f"user_{user_id}/{timestamp}_{filename}"
                            ok, res = upload_file_to_s3(local_dest, s3_key)
                            if ok:
                                saved_pdf_path = res # Stores the S3 key
                                try:
                                    os.remove(local_dest)
                                except Exception:
                                    pass
                            else:
                                saved_pdf_path = local_dest
                        else:
                            saved_pdf_path = local_dest
                else:
                    # Not saving, use temp path
                    temp_path = f"temp_{filename}"
                    try:
                        file.save(temp_path)
                        text = extract_text_from_pdf(temp_path)
                        if not text:
                            error_message = "Could not read this PDF. It may be a scanned image."
                        else:
                            query_text += "\n" + text
                    except Exception as e:
                        error_message = f"Error processing PDF: {str(e)}"
                    finally:
                        if os.path.exists(temp_path):
                            try:
                                os.remove(temp_path)
                            except Exception:
                                pass

        if query_text.strip() and not error_message:
            analysis_result = translate_discharge(query_text)
            
            # Save to records if requested and not error
            if request.form.get('should_save') == 'yes' and session.get('user'):
                from utils.records_helper import save_report
                user_id = session['user']['id']
                folder_id = request.form.get('folder_id')
                save_title = request.form.get('save_title', '').strip() or f"Discharge Summary - {filename if 'filename' in locals() else 'Pasted Text'}"
                
                ok, msg = save_report(
                    user_id=user_id,
                    folder_id=folder_id,
                    report_type='discharge',
                    title=save_title,
                    original_text=query_text,
                    original_pdf_path=saved_pdf_path,
                    analysis_result=analysis_result
                )
                save_success = ok
        elif not error_message:
            error_message = "Please enter some discharge summary notes or upload a PDF."

    return render_template('discharge.html',
                           result=analysis_result,
                           error=error_message,
                           query=query_text,
                           folders=folders,
                           save_success=save_success)

@app.route('/medicine')
def medicine():
    return render_template('medicine.html')

@app.route('/medicine/search', methods=['POST'])
def medicine_search():
    from utils.medicine_finder import find_substitute

    brand = request.form.get('brand_name', '').strip()

    if not brand:
        return render_template('medicine.html',
                               error="Please enter a medicine name.")

    results = find_substitute(brand)
    if results is None:
        return render_template('medicine.html',
                               error="Database error. Please try again.",
                               searched=brand)
    return render_template('medicine.html',
                           results=results,
                           searched=brand)

@app.route('/testreport', methods=['GET', 'POST'])
def testreport():
    analysis_result = None
    error_message = None
    query_text = ""
    folders = []
    save_success = False

    # Get folders if user is logged in
    if session.get('user'):
        from utils.records_helper import get_folders
        folders = get_folders(session['user']['id'])

    if request.method == 'POST':
        query_text = request.form.get('query', '')
        saved_pdf_path = None

        if 'pdf_file' in request.files and request.files['pdf_file'].filename != '':
            file = request.files['pdf_file']

            if not file.filename.lower().endswith('.pdf'):
                error_message = "Please upload a PDF file only."
            else:
                filename = secure_filename(file.filename)
                if not filename:
                    filename = "medical_report.pdf"
                
                # Check if they checked should_save
                should_save = request.form.get('should_save') == 'yes' and session.get('user')
                
                if should_save:
                    # Save to permanent uploads directory
                    import time
                    user_id = session['user']['id']
                    timestamp = int(time.time())
                    stored_filename = f"user_{user_id}_{timestamp}_{filename}"
                    
                    # Ensure uploads dir exists
                    uploads_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'uploads')
                    if not os.path.exists(uploads_dir):
                        os.makedirs(uploads_dir)
                        
                    local_dest = os.path.join(uploads_dir, stored_filename)
                    file.save(local_dest)
                    
                    # Extract text BEFORE uploading to S3 and deleting local file!
                    text = extract_text_from_pdf(local_dest)
                    if not text:
                        error_message = "Could not read this PDF. It may be a scanned image."
                        try:
                            os.remove(local_dest)
                        except Exception:
                            pass
                    else:
                        query_text += "\n" + text
                        
                        # Try S3 upload if configured
                        from utils.s3_helper import upload_file_to_s3, is_s3_configured
                        if is_s3_configured():
                            s3_key = f"user_{user_id}/{timestamp}_{filename}"
                            ok, res = upload_file_to_s3(local_dest, s3_key)
                            if ok:
                                saved_pdf_path = res # Stores S3 key
                                try:
                                    os.remove(local_dest)
                                except Exception:
                                    pass
                            else:
                                saved_pdf_path = local_dest
                        else:
                            saved_pdf_path = local_dest
                else:
                    # Not saving, use temp path
                    temp_path = f"temp_{filename}"
                    try:
                        file.save(temp_path)
                        text = extract_text_from_pdf(temp_path)
                        if not text:
                            error_message = "Could not read this PDF. It may be a scanned image."
                        else:
                            query_text += "\n" + text
                    except Exception as e:
                        error_message = f"Error processing PDF: {str(e)}"
                    finally:
                        if os.path.exists(temp_path):
                            try:
                                os.remove(temp_path)
                            except Exception:
                                pass

        if query_text.strip() and not error_message:
            analysis_result = explain_medical_report(query_text)
            
            # Save to records if requested and not error
            if request.form.get('should_save') == 'yes' and session.get('user'):
                from utils.records_helper import save_report
                user_id = session['user']['id']
                folder_id = request.form.get('folder_id')
                save_title = request.form.get('save_title', '').strip() or f"Medical Report - {filename if 'filename' in locals() else 'Pasted Text'}"
                
                ok, msg = save_report(
                    user_id=user_id,
                    folder_id=folder_id,
                    report_type='lab_report',
                    title=save_title,
                    original_text=query_text,
                    original_pdf_path=saved_pdf_path,
                    analysis_result=analysis_result
                )
                save_success = ok
        elif not error_message:
            error_message = "Please upload a medical report PDF."

    return render_template('testreport.html',
                           result=analysis_result,
                           error=error_message,
                           query=query_text,
                           folders=folders,
                           save_success=save_success)

@app.route('/symptoms', methods=['GET', 'POST'])
def symptoms():
    from utils.ai_helper import analyse_symptoms

    result = None
    error = None
    location = ""

    if request.method == 'POST':
        symptoms_text = request.form.get('symptoms', '').strip()
        location = request.form.get('location', '').strip()

        if not symptoms_text:
            error = "Please describe your symptoms."
        else:
            result = analyse_symptoms(symptoms_text)

    return render_template('symptoms.html',
                           result=result,
                           error=error,
                           location=location)

@app.route('/find-doctors')
def find_doctors():
    from utils.doctor_finder import find_nearby_doctors
    specialist = request.args.get('specialist', 'hospital')
    lat = request.args.get('lat')
    lon = request.args.get('lon')

    if not lat or not lon:
        return jsonify([])

    try:
        doctors = find_nearby_doctors(specialist, float(lat), float(lon))
        # If no specific specialist doctors are found, fallback to generic hospitals
        if not doctors and specialist != 'hospital':
            doctors = find_nearby_doctors('hospital', float(lat), float(lon))
        return jsonify(doctors)
    except Exception as e:
        print(f"Error in /find-doctors route: {e}")
        return jsonify([])

@app.route('/register', methods=['GET', 'POST'])
def register():
    if session.get('user'):
        return redirect('/dashboard')

    error = None
    success = None
    email = ""

    if request.method == 'POST':
        from utils.auth_helper import register_user
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        if not email or not password:
            error = "Email and password are required."
        elif password != confirm_password:
            error = "Passwords do not match."
        elif len(password) < 6:
            error = "Password must be at least 6 characters long."
        else:
            ok, msg = register_user(email, password)
            if ok:
                return render_template('login.html', success="Registration successful! Please log in below.")
            else:
                error = msg

    return render_template('register.html', error=error, success=success, email=email)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('user'):
        return redirect('/dashboard')

    error = None
    email = ""

    if request.method == 'POST':
        from utils.auth_helper import authenticate_user
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')

        if not email or not password:
            error = "Email and password are required."
        else:
            ok, res = authenticate_user(email, password)
            if ok:
                session['user'] = res
                return redirect('/dashboard')
            else:
                error = res

    return render_template('login.html', error=error, email=email)

@app.route('/logout')
def logout():
    session.pop('user', None)
    session.pop('guest', None)
    return redirect('/')

@app.route('/guest')
def guest():
    session['guest'] = True
    return redirect('/dashboard')

@app.route('/admin/users')
def admin_users():
    if not session.get('user'):
        return redirect('/')
        
    from utils.auth_helper import get_db
    conn = None
    cursor = None
    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        
        # Get total users count
        cursor.execute("SELECT COUNT(*) AS total FROM users")
        count_res = cursor.fetchone()
        total_count = count_res['total'] if count_res else 0
        
        # Get user details
        cursor.execute("SELECT id, email, created_at FROM users ORDER BY created_at DESC")
        users = cursor.fetchall()
        
        return render_template('admin_users.html', total_count=total_count, users=users)
    except Exception as e:
        print(f"DATABASE ERROR in admin_users: {e}")
        return render_template('admin_users.html', error=f"Could not load users database. Error: {str(e)}", total_count=0, users=[])
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route('/records')
def records():
    if not session.get('user'):
        return redirect('/')
        
    user_id = session['user']['id']
    folder_id = request.args.get('folder_id')
    
    from utils.records_helper import get_folders, get_reports
    folders = get_folders(user_id)
    
    active_folder = None
    active_folder_id = None
    if folder_id:
        try:
            active_folder_id = int(folder_id)
            for f in folders:
                if f['id'] == active_folder_id:
                    active_folder = f
                    break
        except ValueError:
            pass
            
    reports = get_reports(user_id, active_folder_id)
    
    error = request.args.get('error')
    success = request.args.get('success')
    
    return render_template('records.html',
                           folders=folders,
                           reports=reports,
                           active_folder_id=active_folder_id,
                           active_folder=active_folder,
                           error=error,
                           success=success)

@app.route('/folders/create', methods=['POST'])
def create_new_folder_route():
    if not session.get('user'):
        return redirect('/')
        
    user_id = session['user']['id']
    folder_name = request.form.get('folder_name', '').strip()
    
    from utils.records_helper import create_folder
    ok, msg = create_folder(user_id, folder_name)
    if ok:
        return redirect('/records?success=' + msg)
    else:
        return redirect('/records?error=' + msg)

@app.route('/folders/delete/<int:folder_id>', methods=['POST'])
def delete_folder_route(folder_id):
    if not session.get('user'):
        return redirect('/')
        
    user_id = session['user']['id']
    from utils.records_helper import delete_folder
    ok, msg = delete_folder(user_id, folder_id)
    if ok:
        return redirect('/records?success=' + msg)
    else:
        return redirect('/records?error=' + msg)

@app.route('/records/delete/<int:report_id>', methods=['POST'])
def delete_report_route(report_id):
    if not session.get('user'):
        return redirect('/')
        
    user_id = session['user']['id']
    from utils.records_helper import delete_report
    ok, msg = delete_report(user_id, report_id)
    if ok:
        return redirect('/records?success=' + msg)
    else:
        return redirect('/records?error=' + msg)

@app.route('/records/view/<int:report_id>')
def view_saved_report(report_id):
    if not session.get('user'):
        return redirect('/')
        
    user_id = session['user']['id']
    from utils.records_helper import get_report_details
    report = get_report_details(user_id, report_id)
    
    if not report:
        return redirect('/records?error=Report not found.')
        
    pdf_url = None
    pdf_path = report.get('original_pdf_path')
    if pdf_path:
        if os.path.exists(pdf_path):
            filename = os.path.basename(pdf_path)
            pdf_url = f"/uploads/{filename}"
        else:
            from utils.s3_helper import get_s3_presigned_url, is_s3_configured
            if is_s3_configured():
                pdf_url = get_s3_presigned_url(pdf_path)
                
    return render_template('view_report.html', report=report, pdf_url=pdf_url)

@app.route('/uploads/<filename>')
def serve_upload(filename):
    if not session.get('user'):
        return redirect('/')
        
    from flask import send_from_directory
    uploads_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'uploads')
    return send_from_directory(uploads_dir, filename)

# ── RUN ─────────────────────────────────────────────

if __name__ == '__main__':
    app.run(port=8081, debug=True)