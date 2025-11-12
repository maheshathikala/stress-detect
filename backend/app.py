# app.py (fixed: no truthy tests on PyMongo collections)
import os
from datetime import datetime
import random
import io
import base64
import secrets as _secrets  # only for fallback secret generation during dev

from flask import Flask, render_template, request, jsonify, session, redirect, url_for, Response
from flask_cors import CORS
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
import cv2
import numpy as np
from tensorflow.keras.preprocessing.image import img_to_array
from tensorflow.keras.models import load_model
from PIL import Image
from bson import ObjectId

# Optional: load .env in development
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

# --------- Environment ----------
ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'admin')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', '')  # empty by default if not set

MONGO_URI = os.environ.get('MONGO_URI', 'mongodb://localhost:27017/')
DB_NAME = os.environ.get('DB_NAME', 'stress_detection_db')

MODEL_PATH = os.environ.get('MODEL_PATH', os.path.join("backend", "scripts", "emotion_model.h5"))

FLASK_DEBUG = os.environ.get('FLASK_DEBUG', 'False').lower() in ('1', 'true', 'yes')
FLASK_PORT = int(os.environ.get('FLASK_PORT', 5000))

# SECRET_KEY - use env if present, otherwise fallback to a generated key (not for production)
SECRET_KEY = os.environ.get('SECRET_KEY') or _secrets.token_hex(16)

# --------- Flask ----------
app = Flask(__name__)
app.secret_key = SECRET_KEY
CORS(app, supports_credentials=True)

# --------- MongoDB ----------
try:
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    users_collection = db['users']
    stress_logs_collection = db['stress_logs']
except Exception as e:
    print(f"MongoDB connection error: {e}")
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
        print(f"✅ Emotion model loaded successfully from: {model_path_abs}")
    else:
        raise FileNotFoundError(f"Model not found at: {model_path_abs}")

    emotion_labels = ['Angry', 'Disgust', 'Fear', 'Happy', 'Sad', 'Surprise', 'Neutral']
except Exception as e:
    print(f"Error loading models: {e}")
    emotion_model = None
    emotion_labels = []

# -------------------- ROUTES --------------------

@app.route('/')
def index():
    return render_template('login.html')

@app.route('/register', methods=['POST'])
def register():
    # DB guard
    if users_collection is None:
        return jsonify({'success': False, 'message': 'Database unavailable'}), 500
    try:
        data = request.get_json(force=True)
        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            return jsonify({'success': False, 'message': 'Username and password are required'}), 400

        if users_collection.find_one({'username': username}):
            return jsonify({'success': False, 'message': 'Username already exists'}), 400

        hashed_password = generate_password_hash(password)
        users_collection.insert_one({
            'username': username,
            'password': hashed_password,
            'role': 'user',
            'created_at': datetime.utcnow()
        })
        return jsonify({'success': True, 'message': 'Registration successful'})
    except Exception as e:
        return jsonify({'success': False, 'message': f"Registration error: {str(e)}"}), 500

@app.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json(force=True)
        username = data.get('username')
        password = data.get('password')

        # Super-admin from environment (doesn't touch DB)
        if ADMIN_USERNAME and ADMIN_PASSWORD and username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['user_id'] = 'admin'
            session['username'] = username
            session['role'] = 'admin'
            return jsonify({'success': True, 'role': 'admin', 'message': 'Admin login successful'})

        # DB users (explicit None check for collection)
        if users_collection is None:
            return jsonify({'success': False, 'message': 'Database unavailable'}), 500

        user = users_collection.find_one({'username': username})
        if user and check_password_hash(user['password'], password):
            session['user_id'] = str(user['_id'])
            session['username'] = username
            session['role'] = user.get('role', 'user')
            return jsonify({'success': True, 'role': session['role'], 'message': 'Login successful'})

        return jsonify({'success': False, 'message': 'Invalid credentials'}), 401
    except Exception as e:
        return jsonify({'success': False, 'message': f"Login error: {str(e)}"}), 500

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
    session.clear()
    return redirect(url_for('index'))

@app.route('/stress-detection')
def stress_detection_page():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    return render_template('stress-detection.html', username=session['username'])

# -------------------- ADMIN ROUTES --------------------

@app.route('/api/users', methods=['GET'])
def get_users():
    if session.get('role') != 'admin':
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
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/users', methods=['POST'])
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

        if not username or not password:
            return jsonify({'success': False, 'message': 'Username and password required'}), 400
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
        return jsonify({'success': True, 'message': 'User created'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/users/<user_id>', methods=['PUT', 'PATCH'])
def update_user(user_id):
    if session.get('role') != 'admin':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    if users_collection is None:
        return jsonify({'success': False, 'message': 'Database unavailable'}), 500
    try:
        data = request.get_json(force=True)
        updates = {}

        if 'username' in data:
            new_username = (data.get('username') or '').strip()
            if not new_username:
                return jsonify({'success': False, 'message': 'Username cannot be empty'}), 400
            existing = users_collection.find_one({'username': new_username, '_id': {'$ne': ObjectId(user_id)}})
            if existing:
                return jsonify({'success': False, 'message': 'Username already in use'}), 400
            updates['username'] = new_username

        if 'email' in data:
            updates['email'] = data.get('email') or None

        if 'role' in data:
            new_role = (data.get('role') or 'user').lower()
            if new_role not in ('user', 'admin'):
                return jsonify({'success': False, 'message': 'Invalid role'}), 400

            target = users_collection.find_one({'_id': ObjectId(user_id)})
            if not target:
                return jsonify({'success': False, 'message': 'User not found'}), 404

            # Prevent removing the last DB admin
            if target.get('role') == 'admin' and new_role != 'admin':
                admin_count = users_collection.count_documents({'role': 'admin'})
                if admin_count <= 1:
                    return jsonify({'success': False, 'message': 'At least one admin must remain'}), 400

            updates['role'] = new_role

        if 'password' in data and (data.get('password') or '').strip():
            updates['password'] = generate_password_hash(data['password'])

        if not updates:
            return jsonify({'success': False, 'message': 'No updates provided'}), 400

        result = users_collection.update_one({'_id': ObjectId(user_id)}, {'$set': updates})
        if result.matched_count == 0:
            return jsonify({'success': False, 'message': 'User not found'}), 404

        return jsonify({'success': True, 'message': 'User updated'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/users/<user_id>', methods=['DELETE'])
def delete_user(user_id):
    if session.get('role') != 'admin':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    if users_collection is None:
        return jsonify({'success': False, 'message': 'Database unavailable'}), 500
    try:
        target = users_collection.find_one({'_id': ObjectId(user_id)})
        if not target:
            return jsonify({'success': False, 'message': 'User not found'}), 404

        # Don’t allow deleting admin users
        if target.get('role') == 'admin':
            return jsonify({'success': False, 'message': 'Admin accounts cannot be deleted'}), 400

        result = users_collection.delete_one({'_id': ObjectId(user_id)})
        if result.deleted_count > 0:
            return jsonify({'success': True, 'message': 'User deleted successfully'})
        else:
            return jsonify({'success': False, 'message': 'User not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# -------------------- STRESS DETECTION --------------------

@app.route('/api/detect-stress', methods=['POST'])
def detect_stress():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized'})
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

        # Explicit None check for collection
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
        print("Detection error:", e)
        return jsonify({'success': False, 'message': f'Detection error: {str(e)}'}), 500

@app.route('/api/stress-logs')
def get_stress_logs():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized'})
    if stress_logs_collection is None:
        return jsonify({'success': False, 'message': 'Database unavailable'}), 500
    try:
        if session.get('role') == 'admin':
            logs = list(stress_logs_collection.find().sort('timestamp', -1).limit(50))
        else:
            logs = list(stress_logs_collection.find({'user_id': session['user_id']}).sort('timestamp', -1).limit(20))
        for log in logs:
            log['_id'] = str(log.get('_id'))
            log['timestamp'] = log.get('timestamp').isoformat() if log.get('timestamp') else ''
        return jsonify({'success': True, 'logs': logs}), 200
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# -------------------- HELPERS --------------------

def analyze_stress_with_model(gray_frame, faces):
    try:
        (x, y, w, h) = max(faces, key=lambda f: f[2] * f[3])
        roi_gray = gray_frame[y:y + h, x:x + w]
        roi_gray = cv2.resize(roi_gray, (48, 48))
        roi_gray = roi_gray.astype("float") / 255.0
        roi_gray = img_to_array(roi_gray)
        roi_gray = np.expand_dims(roi_gray, axis=0)

        preds = emotion_model.predict(roi_gray)[0] if emotion_model is not None else np.zeros((7,))
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
        print(f"Model stress analysis error: {e}")
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

# -------------------- OPTIONAL: REAL-TIME VIDEO FEED --------------------
@app.route('/video_feed')
def video_feed():
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

                preds = emotion_model.predict(roi_gray)[0] if emotion_model is not None else np.zeros((7,))
                label = emotion_labels[np.argmax(preds)] if emotion_labels else "Unknown"
                cv2.putText(frame, label, (x, y - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

            _, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(debug=FLASK_DEBUG, port=FLASK_PORT)
