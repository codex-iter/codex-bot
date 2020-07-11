import os
# import json
import requests
from loguru import logger
# from random import randint
from dotenv import load_dotenv
from pymongo import MongoClient
from flask import Flask, request
from gevent.pywsgi import WSGIServer
from settings import RULES, BOT_INTRO

load_dotenv()

app = Flask(__name__)

TOKEN = os.environ.get('TOKEN')
DB_URI = os.environ.get('DB_URI')
BASE_URL = "https://api.telegram.org/bot{}/".format(TOKEN)
GROUP_CHAT_ID = int(os.environ.get('GROUP_CHAT_ID'))
PAYLOAD = {
    'chat_id': GROUP_CHAT_ID,
}

client = MongoClient(DB_URI, retryWrites=False)
db = client.get_default_database()
members = db.telegram_members


@app.route("/update", methods=["POST"])
def update():
    print("RunningBot.......")
    print(request.get_json())
    data = request.get_json()
    message = data.get('message')
    if message is None:
    	message = data.get('edited_message')

    from_ = int(message.get('from').get('id'))
    group_data = int(message.get('chat').get('id'))
	
    PAYLOAD = {
        'chat_id': GROUP_CHAT_ID,
    }

    logger.debug(GROUP_CHAT_ID)
    logger.debug(group_data)

    if (group_data == GROUP_CHAT_ID) or (group_data == from_):

        print("Working>>>>")

        if 'new_chat_member' in message.keys():
            new_member_name = message.get('new_chat_member').get('first_name')
            new_member_id = message.get('new_chat_member').get('id')

            PAYLOAD['text'] = f"Welcome to CODEX {new_member_name}"

            PAYLOAD_FOR_USER = {
                'chat_id': new_member_id,
                'text': RULES
            }

            requests.post(BASE_URL + "sendMessage", data=PAYLOAD)
            requests.post(BASE_URL + "sendMessage", data=PAYLOAD_FOR_USER)

        if 'text' in message.keys():
            text = message.get('text')
            if text.startswith("/"):
                logger.debug(text)
                [cmd, *args] = text[1:].split()
                if (cmd == 'xkcd') or (cmd == 'xkcd@Alfredcodex_bot'):
                    if not args:
                        PAYLOAD['text'] = "Requires xkcd comic index. Example /xkcd 1001"
                        requests.post(
                            BASE_URL + "sendMessage", data=PAYLOAD)
                    else:
                        if args[0].isdecimal():
                            comic = getXKCD(args[0])
                        else:
                            comic = None
                        if comic:
                            PAYLOAD['caption'] = f"{comic['title']}\n\n{comic['alt']}"
                            PAYLOAD['photo'] = comic['url']
                            requests.post(
                                BASE_URL + "sendPhoto", data=PAYLOAD)
                        else:
                            PAYLOAD['text'] = "Not a valid comic index"
                            requests.post(
                                BASE_URL + "sendMessage", data=PAYLOAD)

                elif (cmd == 'helpme') or (cmd == 'helpme@Alfredcodex_bot'):

                    PAYLOAD = {
                        'chat_id': GROUP_CHAT_ID,
                        'text': BOT_INTRO
                    }

                    requests.post(BASE_URL + "sendMessage", data=PAYLOAD)

                elif (cmd == 'rules') or (cmd == 'rules@Alfredcodex_bot'):

                    chat_id_of_request = message.get('from').get('id')

                    PAYLOAD = {
                        'chat_id': chat_id_of_request,
                        'text': RULES
                    }

                    requests.post(BASE_URL + "sendMessage", data=PAYLOAD)
                elif (cmd == 'register') or (cmd == 'register@Alfredcodex_bot'):

                    user_json = message.get('from')
                    chat_id_of_request = user_json.get('id')
                    logger.debug(args)
                    PAYLOAD = {
                        'chat_id': chat_id_of_request
                    }

                    if len(args):
                        valid_username = validate_github(args[0])

                        if valid_username:
                            userdata = {
                                "github_username": valid_username,
                                "telegram_username": user_json.get("username"),
                                "full_name": f"{user_json.get('first_name')} {user_json.get('last_name')}"}

                            logger.debug(userdata)
                            register = register_github(userdata)
                            if register:
                                PAYLOAD['text'] = f"Registered as {userdata['github_username']}"
                            else:
                                PAYLOAD['text'] = "Could not register."
                        else:
                            PAYLOAD['text'] = "Invalid username. Try again."
                    else:
                        PAYLOAD['text'] = "No username given. Syntax is /register {GithubUsername}"

                    requests.post(BASE_URL + 'sendMessage', data=PAYLOAD)

    return "200, OK"


def getXKCD(index):
    r = requests.get(f"https://xkcd.com/{index}/info.0.json")
    if r.status_code == 200:
        data = r.json()
        url = data.get('img')
        alt = data.get('alt')
        title = data.get('title')
        return {'url': url, 'alt': alt, 'title': title}
    else:
        return None


def validate_github(github_username):
    GITHUB_API = f'https://api.github.com/users/{github_username}'

    r = requests.get(GITHUB_API)

    try:
        if r.json()['login'].lower() == github_username.lower():
            return r.json()['login']
    except KeyError:
        return False


def register_github(userdata):
    try:
        up = members.update_one({"github_username": userdata['github_username']},
                                {"$set": userdata},
                                upsert=True)
    except Exception as e:
        logger.error(e)
        return False

    return up


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    http_server = WSGIServer(('', port), app)
    http_server.serve_forever()
