import re
import telebot
import yaml

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

INFER_MODE = "cpp" 
CHAT_HISTORY = {}



def reply_and_remember(chat_id, infer_type: str, qr: str) -> None:
    if chat_id in CHAT_HISTORY.keys():
        history = CHAT_HISTORY.get(chat_id)
        match infer_type:
            case "tgi":
                response = local_tgi_request(host=LOCAL_TGI_HOST, qr=qr, chat_history=history)
            case "cpp":
                response = local_llamacpp_request(model_path=str(GEMMA), qr=qr, chat_history=history)
            case "claude":
                response = claude_request(token=CLAUDE_TOKEN, qr=qr, chat_history=history)
            case _:
                response = "No such inference mode"

        bot.send_message(chat_id, response)
        history.append((qr, response))
        CHAT_HISTORY[chat_id] = history

        for k, v in CHAT_HISTORY.items():
            if len(CHAT_HISTORY[k]) > 5:
                CHAT_HISTORY[k] = v[-5:]
    else:
        match infer_type:
            case "tgi":
                response = local_tgi_request(host=LOCAL_TGI_HOST, qr=qr)
            case "cpp":
                response = local_llamacpp_request(model_path=str(GEMMA), qr=qr)
            case "claude":
                response = claude_request(token=CLAUDE_TOKEN, qr=qr)
            case _:
                response = "No such inference mode"

        bot.send_message(chat_id, response)
        CHAT_HISTORY[chat_id] = [(qr, response)]


def clear_chat_history(chat_id):
    CHAT_HISTORY[chat_id] = []


def show_chat_history(chat_id=None):
    if chat_id == None:
        return CHAT_HISTORY
    else:
        return CHAT_HISTORY[chat_id]


# Special commands handler
@bot.message_handler(regexp=r"\/", content_types=['text'])
def command_handle_special(message):
    if "/clean_history" in message.text:
        try:
            clear_chat_history(message.chat.id)
            bot.send_message(message.chat.id, f"Conversation history has been wiped out. This is what the conversation history looks like now: {show_chat_history(message.chat.id)}")
        except:
            bot.send_message(message.chat.id, f"Hasn't been given access to edit the conversation history. This is what the conversation history looks like: {show_chat_history(message.chat.id)}")
    elif message.text == "/chat_history":
        try:
            bot.send_message(message.chat.id, f"This is what the conversation history looks like now: {show_chat_history(message.chat.id)}")
        except:
            bot.send_message(message.chat.id, "No conversation history")
    elif message.text == "/full_chat_history":
        try:
            bot.send_message(message.chat.id, f"This is what all conversation histories look like now: {show_chat_history()}")
        except:
            bot.send_message(message.chat.id, "No conversation histories")
    elif "/help" in message.text:
        bot.send_message(message.chat.id, "Use /clean_history to clean the memory of the bot.\nUse /chat_history to show the conversation history.")


# First general handler of messages
@bot.message_handler(content_types=['text'])
def command_handle_text(message):
    # try:
        chat_id = message.chat.id
        msg = message.text
        reply_and_remember(chat_id=chat_id, infer_type=INFER_MODE, qr=msg)
    # except:
    #     bot.send_message(message.chat.id, "No comment.")


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
        reply_and_remember(chat_id=chat_id, infer_type=INFER_MODE, qr=query)
    except Exception:
        bot.send_message(message.chat.id, "File could not be processed.")



bot.polling(none_stop=True, interval=0)