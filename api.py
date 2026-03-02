#!/home/rc/server-stats/.venv/bin/python
import os
import jwt
import datetime
from functools import wraps
from flask import Flask, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv
import system_metrics
import wifi_manager

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY')
DASHBOARD_USERNAME = os.getenv('DASHBOARD_USERNAME')
DASHBOARD_PASSWORD = os.getenv('DASHBOARD_PASSWORD')

CORS(app, origins=[
    "http://localhost:3000", 
    "http://192.168.56.1:3000",
    "https://arkalit.my.id",
    "https://sys.arkalit.my.id"
])

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token or "Bearer " not in token:
            return jsonify({'message': 'Token is missing!'}), 401
        try:
            token_clean = token.split(" ")[1]
            jwt.decode(token_clean, app.config['SECRET_KEY'], algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired!'}), 401
        except:
            return jsonify({'message': 'Token is invalid!'}), 401
        return f(*args, **kwargs)
    return decorated

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    if not data or 'username' not in data or 'password' not in data:
        return jsonify({"message": "Username and Password required"}), 400
    
    if data['username'] == DASHBOARD_USERNAME and data['password'] == DASHBOARD_PASSWORD:
        token = jwt.encode({
            'user': DASHBOARD_USERNAME,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(days=7)
        }, app.config['SECRET_KEY'], algorithm="HS256")
        return jsonify({'token': token})
    
    return jsonify({'message': 'Access Denied: Invalid Credentials'}), 401

@app.route('/api/status', methods=['GET'])
@token_required
def status_endpoint():
    return jsonify(system_metrics.get_full_metrics())

@app.route('/api/wifi/list', methods=['GET'])
@token_required
def wifi_list_endpoint():
    return jsonify(wifi_manager.get_wifi_list())

@app.route('/api/wifi/connect', methods=['POST'])
@token_required
def wifi_connect_endpoint():
    data = request.json
    if not data or 'ssid' not in data or 'password' not in data:
        return jsonify({"status": "error", "message": "Missing SSID or Password"}), 400
    result = wifi_manager.connect_to_wifi(data['ssid'], data['password'])
    return jsonify(result)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)