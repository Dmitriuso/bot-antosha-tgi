import telebot
import yaml

from pathlib import Path
from telebot.apihelper import delete_webhook

from app import sg_request, local_tgi_request

PWD = Path(__file__).parent
CONFIG = PWD / "config.yaml"

# load the config from YML file
with open(CONFIG, 'r') as f:
    yaml_data = yaml.safe_load(f)


LOCAL_TGI_HOST = yaml_data["local_tgi_host"]
SG_HOST = yaml_data["sg_host"]

BOT_TAG = yaml_data["bot_tag"]

bot = telebot.TeleBot(yaml_data["bot_token"], parse_mode=None)
bot.delete_webhook()

chat_history = {}
for k, v in chat_history.items():
    if len(chat_history[k]) > 7:
        chat_history[k] = v[-7:]

@bot.message_handler(content_types=['text'])
def get_text_messages(message):
    if message.text == "/start":
        bot.send_message(message.chat.id, "Здравствуйте, милостивый государь.")
    elif message.text == "/help":
        bot.send_message(message.chat.id, "Как могу я вам помочь?")
    elif message.text == "/clean_history":
        chat_history = {}
        bot.send_message(message.chat.id, "Забыл всё прошлое, начнём с чистого листа")
    elif BOT_TAG in message.text:
        try:
            msg = (message.text).replace(BOT_TAG, "")
            if message.chat.id in chat_history.keys():
                history = chat_history.get(message.chat.id)
                llm_response = local_tgi_request(host=LOCAL_TGI_HOST, qr=msg, chat_history=history) # sg_request(host=SG_HOST, qr=message.text, lang="en", chat_history=history)
                bot.send_message(message.chat.id, llm_response)
                history.append((msg, llm_response))
                chat_history[message.chat.id] = history
            else:
                llm_response = local_tgi_request(host=LOCAL_TGI_HOST, qr=msg) # sg_request(host=SG_HOST, qr=message.text, lang="en")
                bot.send_message(message.chat.id, llm_response)
                chat_history[message.chat.id] = [(msg, llm_response)]
        except Exception:
            bot.send_message(message.chat.id, "Ушёл на переучёт...")
    else:
        pass
        

bot.polling(none_stop=True, interval=0)