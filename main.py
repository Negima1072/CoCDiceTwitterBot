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

quickreply = [
    {
    "label": "help",
    "description": "Show help message",
    "metadata": "external_id_3"
    },
    {
    "label": "1d100",
    "description": "Random from 1 to 100",
    "metadata": "external_id_1"
    },
    {
    "label": "cc<=50",
    "description": "50% success",
    "metadata": "external_id_2"
    },
    {
    "label": "MA",
    "description": "Sample Manias",
    "metadata": "external_id_4"
    }
]

helpmes = """・判定　CC(x)<=（目標値）
　x：ボーナス・ペナルティダイス。省略可。
　目標値が無くても1D100は表示される。
　ファンブル／失敗／　レギュラー成功／ハード成功／
　イクストリーム成功／クリティカル を自動判定。
　例）CC<=30　CC(2)<=50 CC(+2)<=50 CC(-1)<=75 CC-1<=50 CC1<=65 CC+1<=65 CC

・技能ロールの難易度指定　CC(x)<=(目標値)(難易度)
　目標値の後に難易度を指定することで
　成功／失敗／クリティカル／ファンブル を自動判定する。
　難易度の指定：
　　r:レギュラー　h:ハード　e:イクストリーム　c:クリティカル
　例）CC<=70r CC1<=60h CC-2<=50e CC2<=99c

・組み合わせ判定　(CBR(x,y))
　目標値 x と y で％ロールを行い、成否を判定。
　例）CBR(50,20)

・自動火器の射撃判定　FAR(w,x,y,z,d,v)
　w：弾丸の数(1～100）、x：技能値（1～100）、y：故障ナンバー、
　z：ボーナス・ペナルティダイス(-2～2)。省略可。
　d：指定難易度で連射を終える（レギュラー：r,ハード：h,イクストリーム：e）。省略可。
　v：ボレーの弾丸の数を変更する。省略可。
　命中数と貫通数、残弾数のみ算出。ダメージ算出はありません。
例）FAR(25,70,98)　FAR(50,80,98,-1)　far(30,70,99,1,R)
　　far(25,88,96,2,h,5)　FaR(40,77,100,,e,4)　fAr(20,47,100,,,3)

・各種表
　【狂気関連】
　・狂気の発作（リアルタイム）（Bouts of Madness Real Time）　BMR
　・狂気の発作（サマリー）（Bouts of Madness Summary）　BMS
　・恐怖症（Sample Phobias）表　PH／マニア（Sample Manias）表　MA
　【魔術関連】
　・プッシュ時のキャスティング・ロール（Casting Roll）の失敗表
　　強力でない呪文の場合　FCL／強力な呪文の場合　FCM
  
システム共通コマンド
3D6+1>=9 ：3d6+1で目標値9以上かの判定
1D100<=50 ：D100で50％目標の下方ロールの例
3U6[5] ：3d6のダイス目が5以上の場合に振り足しして合計する(上方無限)
3B6 ：3d6のダイス目をバラバラのまま出力する（合計しない）
10B6>=4 ：10d6を振り4以上のダイス目の個数を数える
(8/2)D(4+6)<=(5*3)：個数・ダイス・達成値には四則演算も使用可能
C(10-4*3/2+2)：C(計算式）で計算だけの実行も可能
choice[a,b,c]：列挙した要素から一つを選択表示。ランダム攻撃対象決定などに
S3d6 ：各コマンドの先頭に「S」を付けると他人には見えないシークレットロール
3d6/2 ：ダイス出目を割り算（切り捨て）切り上げは /2U、四捨五入は /2R
D66 ：D66ダイス。順序はゲームに依存（D66N：そのまま、D66S：昇順）
https://docs.bcdice.org/
"""

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
    return "v0.1.4"

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
            if "retweeted_status" not in data["tweet_create_events"][0]:
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
                                    api.send_direct_message(recipient_id=sender_id, text="リプライの続き："+getDiceroll(txt), quick_reply_options=quickreply)
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
                if text == "help":
                    api.send_direct_message(recipient_id=sender_id, text=helpmes, quick_reply_options=quickreply)
                res_text = getDiceroll(text)
                if res_text != "":
                    api.send_direct_message(recipient_id=sender_id, text=res_text, quick_reply_options=quickreply)
        except Exception as e:
            print("Error(DM): "+str(e))
    return 'OK'

if __name__ == '__main__':
    app.run()
