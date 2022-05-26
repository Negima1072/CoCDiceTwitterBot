import os
import base64
import hashlib
import hmac
import json
from flask import Flask, request, jsonify

app = Flask(__name__)

consumer_secret = os.environ.get("CONSUMER_SECRET")

@app.route('/webhook', methods=['GET'])
def webhook_challenge():
    params = request.args
    if 'crc_token' in params:
        sha256_hash_digest = hmac.new(consumer_secret.encode(), msg = params.get('crc_token').encode(), digestmod = hashlib.sha256).digest()
        response_token = 'sha256=' + base64.b64encode(sha256_hash_digest).decode()
        response = {'response_token': response_token}
        return json.dumps(response), 200, {'Content-Type': 'application/json'}
    else:
        return jsonify({"error":"No Content"})

if __name__ == '__main__':
    app.run()