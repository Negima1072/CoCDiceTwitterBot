import json
import tweepy
import datetime
import os
import requests
import schedule
import time
import psycopg2
from xml.sax.saxutils import unescape

from dotenv import load_dotenv
load_dotenv(override=True)


API_KEY = os.getenv('API_KEY')
API_SECRET = os.getenv('API_SECRET')
ACCESS_TOKEN = os.getenv('ACCESS_TOKEN')
ACCESS_SECRET = os.getenv('ACCESS_SECRET')

DBURL = os.getenv('DATABASE_URL')

def get_connection(): 
    return psycopg2.connect(DBURL)

conn = get_connection() 
cur = conn.cursor()

cur.execute('SELECT * FROM data WHERE id = 1')
rows = cur.fetchall()

lasttweet_id = rows[0][0]
lastdm_id = rows[0][1]

cur.close()
conn.close()

auth = tweepy.OAuthHandler(API_KEY, API_SECRET)
auth.set_access_token(ACCESS_TOKEN, ACCESS_SECRET)
api = tweepy.API(auth)

#API
def getDiceroll(command):
    res=requests.get("https://bcdice.kazagakure.net/v2/game_system/Cthulhu7th/roll?command="+command).json()
    if res["ok"]:
        return res["text"]
    return ""

#Mentions
def doReplyMention():
    global lasttweet_id
    status = api.mentions_timeline(since_id=lasttweet_id)
    for mention in status:
        try:
            lasttweet_id = mention.id
            text = unescape(mention.text)
            if " " not in text:
                continue
            txt = ""
            for i in text.split(" "):
                if i[0] != "@":
                    txt+=i
                    txt+=" "
            res_text = getDiceroll(txt)
            if res_text == "":
                continue
            print(mention.id)
            reply_text = "@"+str(mention.user.screen_name) + " " + res_text
            if len(reply_text) > 140:
                replay_text2 = reply_text[0:139] + "…"
            else:
                replay_text2 = reply_text
            api.update_status(status = replay_text2, in_reply_to_status_id = mention.id)
        except Exception as ex:
            print(ex)

#DM
def doReplyDM():
    global lastdm_id
    meses = api.get_direct_messages()
    for mes in meses:
        try:
            if int(mes.id) <= int(lastdm_id):
                continue
            lastdm_id = mes.id
            if mes.message_create["sender_id"] == "1461318388433956865":
                continue
            text = unescape(mes.message_create["message_data"]["text"])
            res_text = getDiceroll(text)
            if res_text == "":
                continue
            print(lastdm_id)
            api.send_direct_message(mes.message_create["sender_id"], res_text)
        except Exception as ex:
            print(ex)

#Update
def updateDB():
    try:
        global lasttweet_id
        global lastdm_id
        conn = get_connection() 
        cur = conn.cursor()
        cur.execute('UPDATE data SET last_tweetid = %s, last_dmid = %s WHERE id = 1', (lasttweet_id, lastdm_id)) 
        conn.commit()
        cur.close()
        conn.close()
    except:
        print("DB Error...")

def job():
    print("do Job" + datetime.datetime.now().strftime('%Y年%m月%d日 %H:%M:%S'))
    try:
        doReplyMention()
        doReplyDM()
        updateDB()
    except Exception as ex:
        print(ex)

schedule.every(60).seconds.do(job)

while True:
    schedule.run_pending()
    time.sleep(1)

