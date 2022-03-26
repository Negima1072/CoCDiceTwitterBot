import json
import tweepy
import datetime
import os
import requests
import schedule
import time
import psycopg2
from xml.sax.saxutils import unescape

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
        lasttweet_id = mention.id
        reply_text = "@"+str(mention.user.screen_name) + " " + res_text
        api.update_status(status = reply_text, in_reply_to_status_id = mention.id)

#DM
def doReplyDM():
    global lastdm_id
    meses = api.get_direct_messages()
    for mes in meses:
        if int(mes.id) <= int(lastdm_id):
            continue
        if mes.message_create["sender_id"] == "1461318388433956865":
            continue
        text = unescape(mes.message_create["message_data"]["text"])
        res_text = getDiceroll(text)
        if res_text == "":
            continue
        lastdm_id = mes.id
        api.send_direct_message(mes.message_create["sender_id"], res_text)

#Update
def updateDB():
    global lasttweet_id
    global lastdm_id
    conn = get_connection() 
    cur = conn.cursor()
    cur.execute('UPDATE data SET last_tweetid = %s, last_dmid = %s WHERE id = 1', (lasttweet_id, lastdm_id)) 
    conn.commit()
    cur.close()
    conn.close()

def job():
    doReplyMention()
    doReplyDM()
    updateDB()

schedule.every(45).seconds.do(job)

while True:
    schedule.run_pending()
    time.sleep(1)

