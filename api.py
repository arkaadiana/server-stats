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
import ssh_monitor
import ai_service

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY')
DASHBOARD_USERNAME = os.getenv('DASHBOARD_USERNAME')
DASHBOARD_PASSWORD = os.getenv('DASHBOARD_PASSWORD')

CORS(app, origins=["http://localhost:3000", "http://192.168.56.1:3000", "https://arkalit.my.id", "https://sys.arkalit.my.id"])

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token or "Bearer " not in token:
            return jsonify({'message': 'Token is missing!'}), 401
        try:
            token_clean = token.split(" ")[1]
            jwt.decode(token_clean, app.config['SECRET_KEY'], algorithms=["HS256"])
        except:
            return jsonify({'message': 'Token is invalid!'}), 401
        return f(*args, **kwargs)
    return decorated

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    if data['username'] == DASHBOARD_USERNAME and data['password'] == DASHBOARD_PASSWORD:
        token = jwt.encode({'user': DASHBOARD_USERNAME, 'exp': datetime.datetime.utcnow() + datetime.timedelta(days=7)}, app.config['SECRET_KEY'], algorithm="HS256")
        return jsonify({'token': token})
    return jsonify({'message': 'Access Denied'}), 401

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
    return jsonify(wifi_manager.connect_to_wifi(data['ssid'], data['password']))

@app.route('/api/ssh/logs', methods=['GET'])
@token_required
def ssh_logs_endpoint():
    return jsonify(ssh_monitor.get_ssh_logs())

@app.route('/api/ai/chat', methods=['POST'])
@token_required
def ai_chat_endpoint():
    data = request.json
    user_message = data['message']
    
    fast_context = system_metrics.get_fast_metrics()
    
    if not fast_context:
        fast_context = system_metrics.get_full_metrics()

    hersi_response = ai_service.process_hersi_request(user_message, fast_context)
    return jsonify(hersi_response)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)