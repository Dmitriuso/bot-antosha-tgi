import re
import telebot
import yaml

from fastapi import HTTPException, status
from pathlib import Path

from app import sg_request, local_tgi_request, local_llamacpp_request, claude_request, extract_normalize, extract_text

RGX = re.compile(r"Antosha|Антошк?а")

PWD = Path(__file__).parent

FILES = PWD / "files"
FILES.mkdir(parents=False, exist_ok=True)

CPP_MODELS = PWD / "cpp_models"
GEMMA = CPP_MODELS / "gemma_2b/gemma-2b.gguf"

CONFIG = PWD / "config.yaml"

# load the config from YML file: config is not commited in a project, you should add it manually
with open(CONFIG, 'r') as f:
    yaml_data = yaml.safe_load(f)


LOCAL_TGI_HOST = yaml_data["local_tgi_host"]
CLAUDE_TOKEN = yaml_data["claude_token"]

SG_HOST = yaml_data["sg_host"]

BOT_TAG = yaml_data["bot_tag"]

bot = telebot.TeleBot(yaml_data["bot_token"], parse_mode=None)
bot.delete_webhook()

chat_history = {}
for k, v in chat_history.items():
    if len(chat_history[k]) > 7:
        chat_history[k] = v[-7:]


def reply_and_remember(chat_id, infer_type: str, qr: str) -> None:
    if chat_id in chat_history.keys():
        history = chat_history.get(chat_id)
        match infer_type:
            case "tgi":
                response = local_tgi_request(host=LOCAL_TGI_HOST, qr=qr, chat_history=history)
            case "cpp":
                response = local_llamacpp_request(model_path=GEMMA, qr=qr, chat_history=history)
            case "claude":
                response = claude_request(token=CLAUDE_TOKEN, qr=qr, chat_history=history)
            case _:
                response = "No such inference mode"
                
        bot.send_message(chat_id, response)
        history.append((qr, response))
        chat_history[chat_id] = history
    else:
        match infer_type:
            case "tgi":
                response = local_tgi_request(host=LOCAL_TGI_HOST, qr=qr)
            case "cpp":
                response = local_llamacpp_request(model_path=GEMMA, qr=qr)
            case "claude":
                response = claude_request(token=CLAUDE_TOKEN, qr=qr)
            case _:
                response = "No such inference mode"
        bot.send_message(chat_id, response)
        chat_history[chat_id] = [(qr, response)]


# Special commands handler
@bot.message_handler(regexp=r"\/", content_types=['text'])
def command_handle_special(message):
    if "/clean_history" in message.text:
        chat_history = {}
        bot.send_message(message.chat.id, "Conversation history has been cleared.")
    elif "/help" in message.text:
        bot.send_message(message.chat.id, "Use /clean_history to clean the memory of the bot.")


# First general handler of messages
@bot.message_handler(content_types=['text'])
def command_handle_text(message):
    try:
        chat_id = message.chat.id
        msg = message.text
        reply_and_remember(chat_id=chat_id, qr=msg)
    except Exception:
        bot.send_message(message.chat.id, "No comment.")


# Handle all sent documents of type 'application/pdf'.
@bot.message_handler(func=lambda message: message.document.mime_type=='application/pdf', content_types=['document'])
def command_handle_pdf(message):
    try:
        file_name = message.document.file_name
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        with open(FILES / file_name, 'wb') as new_file:
            new_file.write(downloaded_file)
            new_file.close()
        
        text = extract_normalize(str(FILES / file_name))
        msg = message.caption
        query = f"{msg}\n{file_name}\n{text}"
        chat_id = message.chat.id
        reply_and_remember(chat_id=chat_id, qr=query)
    except Exception:
        bot.send_message(message.chat.id, "File could not be processed.")



bot.polling(none_stop=True, interval=0)