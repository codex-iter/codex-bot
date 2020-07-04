import os
import requests
from loguru import logger
from random import randint
from dotenv import load_dotenv
from flask import Flask, request
from gevent.pywsgi import WSGIServer
from settings import RULES, BOT_INTRO

load_dotenv()

app = Flask(__name__)

TOKEN = os.environ.get('TOKEN')
BASE_URL = "https://api.telegram.org/bot{}/".format(TOKEN)
GROUP_CHAT_ID = int(os.environ.get('GROUP_CHAT_ID'))
PAYLOAD = {
		'chat_id': GROUP_CHAT_ID,
	}

@app.route("/update", methods = ["POST"])
def update():
	print("RunningBot.......")
	print(request.get_json())
	data = request.get_json()
	message = data.get('message')
	group_data = int(message.get('chat').get('id'))
	
	PAYLOAD = {
		'chat_id': GROUP_CHAT_ID,
	}

	logger.debug(GROUP_CHAT_ID)
	logger.debug(group_data)

	if group_data == GROUP_CHAT_ID:

		print("Working>>>>")

		if 'new_chat_member' in message.keys():
			new_member_name = message.get('new_chat_member').get('first_name')
			new_member_id = message.get('new_chat_member').get('id')
			
			PAYLOAD['text'] = f"Welcome to CODEX {new_member_name}"

			PAYLOAD_FOR_USER = {
			'chat_id': new_member_id,
			'text': RULES
			}

			r = requests.post(BASE_URL+ "sendMessage", data=PAYLOAD)
			r = requests.post(BASE_URL+ "sendMessage", data=PAYLOAD_FOR_USER)
			
		
		if 'text' in message.keys():
			text = message.get('text')
			if text.startswith("/"):
				logger.debug(text)
				[cmd, *args] = text[1:].split()
				if (cmd == 'xkcd') or (cmd == 'xkcd@Alfredcodex_bot'):
					if not args:
						PAYLOAD['text'] = "Requires xkcd comic index. Example /xkcd 1001"
						r = requests.post(BASE_URL + "sendMessage", data=PAYLOAD)
					else:
						if args[0].isdecimal():
							comic = getXKCD(args[0])
						else:
							comic = None
						if comic:
							PAYLOAD['caption'] = f"{comic['title']}\n\n{comic['alt']}"
							PAYLOAD['photo'] = comic['url']
							r = requests.post(BASE_URL + "sendPhoto", data=PAYLOAD)
						else:
							PAYLOAD['text'] = "Not a valid comic index"
							r = requests.post(BASE_URL + "sendMessage", data=PAYLOAD)
		
				elif (cmd =='helpme') or (cmd == 'helpme@Alfredcodex_bot'):
					
					PAYLOAD = {
					'chat_id': GROUP_CHAT_ID,
					'text': BOT_INTRO
					}

					r = requests.post(BASE_URL + "sendMessage", data=PAYLOAD)

				elif (cmd == 'rules') or (cmd == 'rules@Alfredcodex_bot'):
					
					chat_id_of_request = message.get('from').get('id')

					PAYLOAD = {
					'chat_id': chat_id_of_request,
					'text': RULES
					}

					r = requests.post(BASE_URL + "sendMessage", data=PAYLOAD)
				elif (cmd == 'register') or (cmd == 'register@Alfredcodex_bot'):

					user_json = message.get('from')
					chat_id_of_request = user_json.get('id')
					logger.debug(args)
					PAYLOAD = {
							'chat_id': chat_id_of_request
						}

					if len(args):
						valid_username = register_github(args[0])

						userdata = {"github_username" : args[0],
									"telegram_username" : user_json.get("username"),
									"full_name": f"{user_json.get('first_name')} {user_json.get('last_name')}"}

						logger.debug(userdata)

						if valid_username:
							PAYLOAD['text'] = json.dumps(userdata)
						else:
							PAYLOAD['text'] = "Invalid username. Try again."
					else:
						PAYLOAD['text'] = "No username given. Syntax is /register {GithubUsername}"

					r = requests.post(BASE_URL + 'sendMessage', data=PAYLOAD)

	
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


def register_github(github_username):
	GITHUB_API = f'https://api.github.com/users/{github_username}'

	r = requests.get(GITHUB_API)

	try:
		if r.json()['login'].lower() == github_username.lower():
			return True
	except KeyError:
		return False


if __name__ == '__main__':
	port = int(os.environ.get('PORT', 5000))
	http_server = WSGIServer(('', port),app)
	http_server.serve_forever() 
