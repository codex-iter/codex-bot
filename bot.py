from flask import Flask, request
from gevent.pywsgi import WSGIServer
from random import randint
from settings import RULES, BOT_INTRO
import requests
import os

app = Flask(__name__)

TOKEN = os.environ.get('TOKEN')
BASE_URL = "https://api.telegram.org/bot{}/".format(TOKEN)
GROUP_CHAT_ID = int(os.environ.get('group_chat_id'))

@app.route("/update", methods = ["POST"])
def update():
	print("RunningBot.......")
	print(request.get_json())
	data = request.get_json()
	group_data = int(data.get('message').get('chat').get('id'))

	if group_data == GROUP_CHAT_ID:

		print("Working>>>>")

		if 'new_chat_member' in data.get('message'):
			new_member_name = data.get('message').get('new_chat_member').get('first_name')
			new_member_id = data.get('message').get('new_chat_member').get('id')
					
			PAYLOAD = {
			'chat_id': GROUP_CHAT_ID,
			'text':  "Welcome to CODEX " + new_member_name + "!"
			}

			PAYLOAD_FOR_USER = {
			'chat_id': new_member_id,
			'text': RULES
			}

			r = requests.post(BASE_URL+ "sendMessage", data=PAYLOAD)
			r = requests.post(BASE_URL+ "sendMessage", data=PAYLOAD_FOR_USER)
			
		
		if 'text' in data.get('message'): 
			if (data.get('message').get('text')== '/xkcd') or (data.get('message').get('text') == '/xkcd@Alfredcodex_bot'):
			
				random = randint(1, 2100)
				i = requests.get("https://xkcd.com/"+str(random)+"/info.0.json")
				if i.status_code == 200:
					image = i.json()
					url = image.get("img")
					text = image.get("alt")
				
					PAYLOAD = {
					'chat_id': GROUP_CHAT_ID,
					'photo': url,
					'caption':text 
					}

					r = requests.post(BASE_URL + "sendPhoto", data=PAYLOAD)
		
		if 'text' in data.get('message'): 
			if (data.get('message').get('text') =='/helpme') or (data.get('message').get('text') == '/helpme@Alfredcodex_bot'):
				
				PAYLOAD = {
				'chat_id': GROUP_CHAT_ID,
				'text': BOT_INTRO
				}

				r = requests.post(BASE_URL + "sendMessage", data=PAYLOAD)

		if 'text' in data.get('message'): 
			if (data.get('message').get('text') == '/rules') or (data.get('message').get('text') == '/rules@Alfredcodex_bot'):
				
				PAYLOAD = {
				'chat_id': GROUP_CHAT_ID,
				'text': RULES
				}

				r = requests.post(BASE_URL + "sendMessage", data=PAYLOAD)
	
	return "200, OK"

if __name__ == '__main__':
	port = int(os.environ.get('PORT', 5000))
	http_server = WSGIServer(('', port),app)
	http_server.serve_forever() 
