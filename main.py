import os
import base64
import hashlib
import hmac
import json
import tweepy
import requests
from flask import Flask, request, jsonify
from xml.sax.saxutils import unescape

app = Flask(__name__)

consumer_secret = os.environ.get("CONSUMER_SECRET")
consumer_key = os.environ.get("CONSUMER_KEY")
access_token = os.environ.get("ACCESS_TOKEN")
access_token_secret = os.environ.get("ACCESS_SECRET")

auth=tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)
api=tweepy.API(auth)

def getDiceroll(command):
    res=requests.get("https://bcdice.kazagakure.net/v2/game_system/Cthulhu7th/roll?command="+command).json()
    if res["ok"]:
        return res["text"]
    return ""

@app.route('/version', methods=['GET'])
def version():
    return "v0.0.16"

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

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_data(as_text=True)
    data = json.loads(data)
    print(str(data))
    if "tweet_create_events" in data:
        try:
            sender_id = data["tweet_create_events"][0]["user"]["id_str"]
            if "1461318388433956865" in [i["id_str"] for i in data["tweet_create_events"][0]["entities"]["user_mentions"]]:
                if not sender_id == "1461318388433956865":
                    text = unescape(data["tweet_create_events"][0]["text"])
                    if " " in text:
                        txt = ""
                        for i in text.split(" "):
                            if i[0] != "@":
                                txt+=i
                                txt+=" "
                        res_text = getDiceroll(txt)
                        if res_text != "":
                            res_text = "@"+str(data["tweet_create_events"][0]["user"]["screen_name"]) + " " + res_text
                            if len(res_text) > 140:
                                res_text = res_text[0:139] + "…"
                            api.update_status(status = res_text, in_reply_to_status_id = data["tweet_create_events"][0]["id"])
                        else:
                            api.update_status(status = "@"+str(data["tweet_create_events"][0]["user"]["screen_name"]) + " " + "エラー：コマンドが正しくありません。", in_reply_to_status_id = data["tweet_create_events"][0]["id"])
        except Exception as e:
            print("Error(Rp): "+str(e))
    if "direct_message_events" in data:
        try:
            sender_id = data["direct_message_events"][0]["message_create"]["sender_id"]
            if not sender_id == "1461318388433956865":
                text = unescape(data["direct_message_events"][0]["message_create"]["message_data"]["text"])
                res_text = getDiceroll(text)
                if res_text != "":
                    api.send_direct_message(recipient_id=sender_id, text=res_text)
        except Exception as e:
            print("Error(DM): "+str(e))
    return 'OK'

if __name__ == '__main__':
    app.run()