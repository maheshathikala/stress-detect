# app_secure.py (RECOMMENDED VERSION WITH SECURITY FIXES)
# To use: rename this to app.py and update imports

import os
import re
from datetime import datetime, timedelta
import random
import io
import base64
import secrets as _secrets
import logging

from flask import Flask, render_template, request, jsonify, session, redirect, url_for, Response
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf.csrf import CSRFProtect
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
import cv2
import numpy as np
from tensorflow.keras.preprocessing.image import img_to_array
from tensorflow.keras.models import load_model
from PIL import Image
from bson import ObjectId

# --------- LOGGING SETUP ---------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Optional: load .env in development
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

# --------- Environment ----------
ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'admin')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', '')
MONGO_URI = os.environ.get('MONGO_URI', 'mongodb://localhost:27017/')
DB_NAME = os.environ.get('DB_NAME', 'stress_detection_db')
MODEL_PATH = os.environ.get('MODEL_PATH', os.path.join("backend", "scripts", "emotion_model.h5"))
FLASK_DEBUG = os.environ.get('FLASK_DEBUG', 'False').lower() in ('1', 'true', 'yes')
FLASK_PORT = int(os.environ.get('FLASK_PORT', 5000))
SECRET_KEY = os.environ.get('SECRET_KEY') or _secrets.token_hex(32)
ALLOWED_ORIGINS = os.environ.get('ALLOWED_ORIGINS', 'http://localhost:5000').split(',')

# --------- Flask Configuration ---------
app = Flask(__name__)
app.secret_key = SECRET_KEY

# ⚠️ CRITICAL: Session Security Configuration
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)
app.config['SESSION_COOKIE_SECURE'] = True  # HTTPS only
app.config['SESSION_COOKIE_HTTPONLY'] = True  # Prevent JS access
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # CSRF protection
app.config['REMEMBER_COOKIE_SECURE'] = True
app.config['REMEMBER_COOKIE_HTTPONLY'] = True

# --------- Security Headers ---------
@app.after_request
def set_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'"
    return response

# --------- CORS Configuration (Restrictive) ---------
CORS(app, 
     resources={r"/api/*": {"origins": ALLOWED_ORIGINS}},
     supports_credentials=True,
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
     max_age=3600)

# --------- Rate Limiting ---------
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

# --------- CSRF Protection ---------
csrf = CSRFProtect(app)

# --------- MongoDB ----------
try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    client.admin.command('ping')  # Test connection
    db = client[DB_NAME]
    users_collection = db['users']
    stress_logs_collection = db['stress_logs']
    logger.info("✅ MongoDB connected successfully")
except Exception as e:
    logger.error(f"MongoDB connection error: {e}")
    client = None
    db = None
    users_collection = None
    stress_logs_collection = None

# --------- Models ----------
try:
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    base_dir = os.path.dirname(__file__) if '__file__' in globals() else os.getcwd()
    model_path_abs = MODEL_PATH if os.path.isabs(MODEL_PATH) else os.path.join(base_dir, MODEL_PATH)
    
    if os.path.exists(model_path_abs):
        emotion_model = load_model(model_path_abs)
        logger.info(f"✅ Emotion model loaded: {model_path_abs}")
    else:
        raise FileNotFoundError(f"Model not found at: {model_path_abs}")
    
    emotion_labels = ['Angry', 'Disgust', 'Fear', 'Happy', 'Sad', 'Surprise', 'Neutral']
except Exception as e:
    logger.error(f"Error loading models: {e}")
    emotion_model = None
    emotion_labels = []

# --------- INPUT VALIDATION HELPERS ---------

def validate_username(username):
    """Username: alphanumeric + underscore, 3-20 chars"""
    if not username or not isinstance(username, str):
        return False
    if not re.match(r'^[a-zA-Z0-9_]{3,20}$', username):
        return False
    return True

def validate_password(password):
    """Min 8 chars, at least 1 uppercase, 1 digit, 1 special char"""
    if not password or len(password) < 8:
        return False, "Password must be at least 8 characters"
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain uppercase letter"
    if not re.search(r'[0-9]', password):
        return False, "Password must contain digit"
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, "Password must contain special character"
    return True, "OK"

def validate_email(email):
    """Basic email validation"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

# --------- ROUTES ----------

@app.route('/')
def index():
    return render_template('login.html')

@app.route('/register', methods=['POST'])
@limiter.limit("5 per hour")
def register():
    if users_collection is None:
        return jsonify({'success': False, 'message': 'Database unavailable'}), 500
    
    try:
        data = request.get_json(force=True)
        username = (data.get('username') or '').strip()
        password = (data.get('password') or '').strip()
        email = (data.get('email') or '').strip() if 'email' in data else None

        # Validation
        if not validate_username(username):
            return jsonify({'success': False, 'message': 'Invalid username (3-20 chars, alphanumeric + underscore)'}), 400
        
        is_valid, msg = validate_password(password)
        if not is_valid:
            return jsonify({'success': False, 'message': msg}), 400
        
        if email and not validate_email(email):
            return jsonify({'success': False, 'message': 'Invalid email format'}), 400

        if users_collection.find_one({'username': username}):
            return jsonify({'success': False, 'message': 'Username already exists'}), 400

        users_collection.insert_one({
            'username': username,
            'email': email,
            'password': generate_password_hash(password),
            'role': 'user',
            'created_at': datetime.utcnow()
        })
        
        logger.info(f"✅ User registered: {username}")
        return jsonify({'success': True, 'message': 'Registration successful'})
    
    except Exception as e:
        logger.error(f"Registration error: {e}")
        return jsonify({'success': False, 'message': 'Registration error'}), 500

@app.route('/login', methods=['POST'])
@limiter.limit("10 per hour")  # Rate limit login attempts
def login():
    try:
        data = request.get_json(force=True)
        username = (data.get('username') or '').strip()
        password = (data.get('password') or '').strip()

        if not username or not password:
            logger.warning(f"Login attempt with missing credentials from {get_remote_address()}")
            return jsonify({'success': False, 'message': 'Invalid credentials'}), 401

        # Super-admin from environment
        if ADMIN_USERNAME and ADMIN_PASSWORD and username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session.permanent = True
            session['user_id'] = 'admin'
            session['username'] = username
            session['role'] = 'admin'
            logger.info(f"✅ Admin login successful")
            return jsonify({'success': True, 'role': 'admin', 'message': 'Login successful'})

        # DB users
        if users_collection is None:
            return jsonify({'success': False, 'message': 'Database unavailable'}), 500

        user = users_collection.find_one({'username': username})
        if user and check_password_hash(user['password'], password):
            session.permanent = True
            session['user_id'] = str(user['_id'])
            session['username'] = username
            session['role'] = user.get('role', 'user')
            logger.info(f"✅ User login: {username}")
            return jsonify({'success': True, 'role': session['role'], 'message': 'Login successful'})

        logger.warning(f"Failed login attempt for user: {username}")
        return jsonify({'success': False, 'message': 'Invalid credentials'}), 401
    
    except Exception as e:
        logger.error(f"Login error: {e}")
        return jsonify({'success': False, 'message': 'Login error'}), 500

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    if session.get('role') == 'admin':
        return render_template('admin.html', username=session['username'])
    else:
        return render_template('dashboard.html', username=session['username'])

@app.route('/logout')
def logout():
    logger.info(f"User logout: {session.get('username')}")
    session.clear()
    return redirect(url_for('index'))

@app.route('/stress-detection')
def stress_detection_page():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    return render_template('stress-detection.html', username=session['username'])

# -------------------- ADMIN ROUTES --------------------

@app.route('/api/users', methods=['GET'])
@limiter.limit("30 per minute")
def get_users():
    if session.get('role') != 'admin':
        logger.warning(f"Unauthorized user access attempt from {get_remote_address()}")
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    if users_collection is None:
        return jsonify({'success': False, 'message': 'Database unavailable'}), 500
    
    try:
        users = list(users_collection.find({}, {'password': 0}))
        for u in users:
            u['_id'] = str(u['_id'])
            if isinstance(u.get('created_at'), datetime):
                u['created_at'] = u['created_at'].isoformat()
        return jsonify({'success': True, 'users': users})
    except Exception as e:
        logger.error(f"Get users error: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/users', methods=['POST'])
@limiter.limit("20 per hour")
def create_user():
    if session.get('role') != 'admin':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    if users_collection is None:
        return jsonify({'success': False, 'message': 'Database unavailable'}), 500
    
    try:
        data = request.get_json(force=True)
        username = (data.get('username') or '').strip()
        password = (data.get('password') or '').strip()
        email = (data.get('email') or None)
        role = (data.get('role') or 'user').lower()

        # Validation
        if not validate_username(username):
            return jsonify({'success': False, 'message': 'Invalid username format'}), 400
        
        is_valid, msg = validate_password(password)
        if not is_valid:
            return jsonify({'success': False, 'message': msg}), 400
        
        if role not in ('user', 'admin'):
            return jsonify({'success': False, 'message': 'Invalid role'}), 400
        
        if users_collection.find_one({'username': username}):
            return jsonify({'success': False, 'message': 'Username already exists'}), 400

        users_collection.insert_one({
            'username': username,
            'email': email,
            'password': generate_password_hash(password),
            'role': role,
            'created_at': datetime.utcnow()
        })
        
        logger.info(f"✅ User created by admin: {username} (role: {role})")
        return jsonify({'success': True, 'message': 'User created'})
    
    except Exception as e:
        logger.error(f"Create user error: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/users/<user_id>', methods=['PUT', 'PATCH'])
@limiter.limit("20 per hour")
def update_user(user_id):
    if session.get('role') != 'admin':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    if users_collection is None:
        return jsonify({'success': False, 'message': 'Database unavailable'}), 500
    
    try:
        # Validate user_id format
        try:
            ObjectId(user_id)
        except:
            return jsonify({'success': False, 'message': 'Invalid user ID'}), 400
        
        data = request.get_json(force=True)
        updates = {}

        if 'username' in data:
            new_username = (data.get('username') or '').strip()
            if not validate_username(new_username):
                return jsonify({'success': False, 'message': 'Invalid username format'}), 400
            
            existing = users_collection.find_one({'username': new_username, '_id': {'$ne': ObjectId(user_id)}})
            if existing:
                return jsonify({'success': False, 'message': 'Username already in use'}), 400
            updates['username'] = new_username

        if 'email' in data:
            email = (data.get('email') or '').strip()
            if email and not validate_email(email):
                return jsonify({'success': False, 'message': 'Invalid email'}), 400
            updates['email'] = email if email else None

        if 'role' in data:
            new_role = (data.get('role') or 'user').lower()
            if new_role not in ('user', 'admin'):
                return jsonify({'success': False, 'message': 'Invalid role'}), 400
            
            target = users_collection.find_one({'_id': ObjectId(user_id)})
            if not target:
                return jsonify({'success': False, 'message': 'User not found'}), 404
            
            if target.get('role') == 'admin' and new_role != 'admin':
                admin_count = users_collection.count_documents({'role': 'admin'})
                if admin_count <= 1:
                    return jsonify({'success': False, 'message': 'At least one admin must remain'}), 400
            
            updates['role'] = new_role

        if 'password' in data and (data.get('password') or '').strip():
            password = data['password'].strip()
            is_valid, msg = validate_password(password)
            if not is_valid:
                return jsonify({'success': False, 'message': msg}), 400
            updates['password'] = generate_password_hash(password)

        if not updates:
            return jsonify({'success': False, 'message': 'No updates provided'}), 400

        result = users_collection.update_one({'_id': ObjectId(user_id)}, {'$set': updates})
        if result.matched_count == 0:
            return jsonify({'success': False, 'message': 'User not found'}), 404
        
        logger.info(f"✅ User updated: {user_id}")
        return jsonify({'success': True, 'message': 'User updated'})
    
    except Exception as e:
        logger.error(f"Update user error: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/users/<user_id>', methods=['DELETE'])
@limiter.limit("20 per hour")
def delete_user(user_id):
    if session.get('role') != 'admin':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    if users_collection is None:
        return jsonify({'success': False, 'message': 'Database unavailable'}), 500
    
    try:
        try:
            ObjectId(user_id)
        except:
            return jsonify({'success': False, 'message': 'Invalid user ID'}), 400
        
        target = users_collection.find_one({'_id': ObjectId(user_id)})
        if not target:
            return jsonify({'success': False, 'message': 'User not found'}), 404
        
        if target.get('role') == 'admin':
            return jsonify({'success': False, 'message': 'Admin accounts cannot be deleted'}), 400
        
        result = users_collection.delete_one({'_id': ObjectId(user_id)})
        if result.deleted_count > 0:
            logger.info(f"✅ User deleted: {user_id}")
            return jsonify({'success': True, 'message': 'User deleted successfully'})
        else:
            return jsonify({'success': False, 'message': 'User not found'}), 404
    
    except Exception as e:
        logger.error(f"Delete user error: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

# -------------------- STRESS DETECTION --------------------

@app.route('/api/detect-stress', methods=['POST'])
@limiter.limit("30 per minute")
def detect_stress():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    try:
        data = request.get_json(force=True)
        if not data or 'image' not in data:
            return jsonify({'success': False, 'message': 'No image provided'}), 400

        image_data = data['image'].split(',')[-1]
        image_bytes = base64.b64decode(image_data)
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")

        cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)

        if len(faces) == 0:
            return jsonify({'success': False, 'message': 'No face detected'}), 200

        stress_level, top_emotion = analyze_stress_with_model(gray, faces)

        if stress_logs_collection is not None:
            stress_logs_collection.insert_one({
                'user_id': session['user_id'],
                'username': session['username'],
                'stress_level': stress_level,
                'detected_emotion': top_emotion,
                'timestamp': datetime.utcnow()
            })

        return jsonify({
            'success': True,
            'stress_level': stress_level,
            'emotion': top_emotion,
            'message': get_stress_message(stress_level)
        })
    
    except Exception as e:
        logger.error(f"Detection error: {e}")
        return jsonify({'success': False, 'message': 'Detection error'}), 500

@app.route('/api/stress-logs')
@limiter.limit("30 per minute")
def get_stress_logs():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    if stress_logs_collection is None:
        return jsonify({'success': False, 'message': 'Database unavailable'}), 500
    
    try:
        if session.get('role') == 'admin':
            logs = list(stress_logs_collection.find().sort('timestamp', -1).limit(100))
        else:
            logs = list(stress_logs_collection.find({'user_id': session['user_id']}).sort('timestamp', -1).limit(50))
        
        for log in logs:
            log['_id'] = str(log.get('_id'))
            log['timestamp'] = log.get('timestamp').isoformat() if log.get('timestamp') else ''
        
        return jsonify({'success': True, 'logs': logs}), 200
    
    except Exception as e:
        logger.error(f"Get logs error: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

# --------- HEALTH CHECK (NO AUTH REQUIRED) ---------
@app.route('/health')
@limiter.exempt
def health_check():
    """Health check endpoint for load balancers"""
    try:
        if client:
            client.admin.command('ping')
            return jsonify({'status': 'healthy', 'db': 'connected'}), 200
        else:
            return jsonify({'status': 'unhealthy', 'db': 'disconnected'}), 503
    except:
        return jsonify({'status': 'unhealthy'}), 503

# --------- VIDEO FEED (PROTECTED) ---------
@app.route('/video_feed')
def video_feed():
    """Protected video feed - requires session"""
    if 'user_id' not in session:
        return "Unauthorized", 401
    
    def generate_frames():
        cap = cv2.VideoCapture(0)
        while True:
            success, frame = cap.read()
            if not success:
                break
            
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, 1.3, 5)

            for (x, y, w, h) in faces:
                roi_gray = cv2.resize(gray[y:y+h, x:x+w], (48, 48))
                roi_gray = roi_gray.astype("float") / 255.0
                roi_gray = img_to_array(roi_gray)
                roi_gray = np.expand_dims(roi_gray, axis=0)

                preds = emotion_model.predict(roi_gray, verbose=0)[0] if emotion_model is not None else np.zeros((7,))
                label = emotion_labels[np.argmax(preds)] if emotion_labels else "Unknown"
                cv2.putText(frame, label, (x, y - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

            _, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

# --------- HELPERS ----------

def analyze_stress_with_model(gray_frame, faces):
    try:
        (x, y, w, h) = max(faces, key=lambda f: f[2] * f[3])
        roi_gray = gray_frame[y:y + h, x:x + w]
        roi_gray = cv2.resize(roi_gray, (48, 48))
        roi_gray = roi_gray.astype("float") / 255.0
        roi_gray = img_to_array(roi_gray)
        roi_gray = np.expand_dims(roi_gray, axis=0)

        preds = emotion_model.predict(roi_gray, verbose=0)[0] if emotion_model is not None else np.zeros((7,))
        emotion_index = int(np.argmax(preds)) if preds is not None else 0
        emotion = emotion_labels[emotion_index] if emotion_labels else "Unknown"

        stress_map = {
            'Angry': 85,
            'Disgust': 75,
            'Fear': 80,
            'Sad': 65,
            'Surprise': 50,
            'Neutral': 40,
            'Happy': 25
        }

        stress_level = stress_map.get(emotion, 50)
        stress_level += random.randint(-5, 5)
        return max(0, min(100, stress_level)), emotion
    except Exception as e:
        logger.error(f"Model analysis error: {e}")
        return random.randint(20, 80), "Unknown"

def get_stress_message(stress_level):
    if stress_level < 30:
        return "Low stress detected. You seem relaxed! 😊"
    elif stress_level < 50:
        return "Mild stress detected. Consider taking short breaks. 😐"
    elif stress_level < 70:
        return "Moderate stress detected. Try relaxation techniques. 😰"
    else:
        return "High stress detected. Please take care of yourself! 😟"

# --------- ERROR HANDLERS ---------
@app.errorhandler(429)
def ratelimit_handler(e):
    logger.warning(f"Rate limit exceeded: {e}")
    return jsonify({'success': False, 'message': 'Too many requests. Please try again later.'}), 429

@app.errorhandler(404)
def not_found(e):
    return jsonify({'success': False, 'message': 'Endpoint not found'}), 404

@app.errorhandler(500)
def server_error(e):
    logger.error(f"Server error: {e}")
    return jsonify({'success': False, 'message': 'Internal server error'}), 500

# --------- MAIN ---------
if __name__ == '__main__':
    # ⚠️ NEVER run with debug=True in production
    if FLASK_DEBUG and os.environ.get('ENV') != 'production':
        logger.warning("⚠️ DEBUG MODE ENABLED - NOT FOR PRODUCTION")
    
    app.run(debug=FLASK_DEBUG, port=FLASK_PORT, host='0.0.0.0')
