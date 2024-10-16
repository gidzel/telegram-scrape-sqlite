from telethon.tl.functions.messages import ImportChatInviteRequest
from telethon.tl.types import PeerUser, PeerChat, PeerChannel, InputChannel
from time import sleep
import telethon_helpers as th
from datetime import datetime
from telegram_dump import TelegramDump
from telethon import errors
from pathlib import Path
import sys
import pandas as pd
import json
import os

settings = None
session_name = input("Enter session name: ")
Path(session_name).mkdir(parents=True, exist_ok=True)

settings_file_name = os.path.join(session_name, "settings.json")

def save_settings():
    global settings
    global settings_file_name
    global session_name
    with open(settings_file_name, "w") as settings_file:
        json.dump(settings, settings_file)

if os.path.isfile(settings_file_name):
    with open(settings_file_name) as settings_file:
        settings = json.load(settings_file)
else:
    settings = {}
    save_settings()

if len(sys.argv) > 1:
    in_file_name = sys.argv[1]
else:
    print("Please append filename for Groups and Channels! Terminating!")
    sys.exit()

try:
    chats_df = pd.read_csv(in_file_name, encoding='utf-8', sep=';')
except Exception as e:
    print(e)
    sys.exit()


file_name = session_name
print(file_name)

client = th.get_client()
td = TelegramDump(client, file_name)

def check_takeout():
    try:
        with client.takeout(finalize=True) as takeout:
            takeout.iter_messages('me')
        return "OK"
    except errors.TakeoutInitDelayError as e:
            print('Must wait', e.seconds, 'before takeout')
            return "TakeoutInitDelayError"
    except errors.TakeoutInvalidError as e:
        print(e)
        return "TakeoutInvalidError"
    
while check_takeout() == "TakeoutInitDelayError":
    input("Allow Takeout in Telegram Messenger and press ENTER")
print("Takeout allowed")

start_date = None
if 'last_scrape' in settings:
    start_date = datetime.strptime(settings['last_scrape'], "%Y-%m-%d")
    print("start_date "+settings['last_scrape'])
else:
    print("scrape from beginning")

count = 0
for index, row in chats_df.iterrows():
    location = row['location']
    category = row['category']
    tme_link = row['link']
    chat_name  = tme_link.split('/')[3]
    print(str(location)+" "+str(chat_name))

    try:
        entity = client.get_entity(chat_name)

        if entity is None:
            print("channel is none")
            continue
        print(entity.title)
    except Exception as e:
        print(e)
        continue

    td.process_chat(
        chat_name=chat_name, 
        chat=entity, 
        location=location, 
        category=category, 
        media=False,
        start_date=start_date
        #end_date=start_date
        )
    count = index
    sleep(3.1)

if count == len(chats_df)-1:
    settings['last_scrape'] = datetime.now().strftime("%Y-%m-%d")
    save_settings()