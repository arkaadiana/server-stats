#!/home/rc/server-stats/.venv/bin/python
from flask import Flask, jsonify, request

import system_metrics
import wifi_manager

app = Flask(__name__)

@app.route('/api/status', methods=['GET'])
def status_endpoint():
    return jsonify(system_metrics.get_full_metrics())

@app.route('/api/wifi/list', methods=['GET'])
def wifi_list_endpoint():
    return jsonify(wifi_manager.get_wifi_list())

@app.route('/api/wifi/connect', methods=['POST'])
def wifi_connect_endpoint():
    data = request.json
    if not data or 'ssid' not in data or 'password' not in data:
        return jsonify({"status": "error", "message": "SSID/Password kosong"}), 400
    
    result = wifi_manager.connect_to_wifi(data['ssid'], data['password'])
    return jsonify(result)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)