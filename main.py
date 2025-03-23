import datetime
import logging
import re
import telebot
import os
import traceback
import yaml

from dotenv import load_dotenv

from pathlib import Path
from typing import AnyStr, Tuple

from app import InferenceManager, extract_normalize, extract_text

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

load_dotenv(override=True)

BOT_TOKEN = os.getenv("BOT_TOKEN")
BOT_TAG = os.getenv("BOT_TAG")

RGX = re.compile(r"Antosha|Антошк?а")

PWD = Path(__file__).parent

FILES = PWD / "files"
FILES.mkdir(parents=False, exist_ok=True)

bot = telebot.TeleBot(BOT_TOKEN, parse_mode=None)
bot.delete_webhook()

INFER_MODE = os.getenv("INFER_MODE")
USER_SYSTEM_PROMPTS = {}
CHAT_HISTORY = {}

HELP_MESSAGE = """
/clean_history : clean the memory of the bot
/chat_history : to show the conversation history
/new_prompt : create your own system prompt
/current_prompt: see currently used system prompt
"""

LANG: str = "EN"

inf_manager = InferenceManager(
    inf_mode=INFER_MODE,
    lang=LANG
)


def reply_and_remember(chat_id, qr: str, user_system_prompt: str | None = None) -> None:
    logger.info(f"\n{datetime.datetime.now()} - {qr}")
    if user_system_prompt:
        if chat_id in CHAT_HISTORY.keys():
            history = CHAT_HISTORY.get(chat_id)
            
            response = inf_manager.infer(prompt=user_system_prompt, qr=qr, chat_history=history)

            bot.send_message(chat_id, response)
            history.append((qr, response))
            CHAT_HISTORY[chat_id] = history

            for k, v in CHAT_HISTORY.items():
                if len(CHAT_HISTORY[k]) > 5:
                    CHAT_HISTORY[k] = v[-5:]
        else:
            response = inf_manager.infer(prompt=user_system_prompt, qr=qr)
            bot.send_message(chat_id, response)
            CHAT_HISTORY[chat_id] = [(qr, response)]

    else:
        if chat_id in CHAT_HISTORY.keys():
            history = CHAT_HISTORY.get(chat_id)

            response = inf_manager.infer(qr=qr, chat_history=history)
            
            bot.send_message(chat_id, response)
            history.append((qr, response))
            CHAT_HISTORY[chat_id] = history

            for k, v in CHAT_HISTORY.items():
                if len(CHAT_HISTORY[k]) > 5:
                    CHAT_HISTORY[k] = v[-5:]
        else:
            response = inf_manager.infer(qr=qr)
            bot.send_message(chat_id, response)
            CHAT_HISTORY[chat_id] = [(qr, response)]


def set_lang(lang: str, chat_id):
    LANG = lang
    if CHAT_HISTORY[chat_id]:
        clear_chat_history(chat_id)
    return LANG


def add_to_chat_history(chat_id, entry: tuple):
    if chat_id in list(CHAT_HISTORY.keys()):
        CHAT_HISTORY[chat_id].append(entry)
    else:
        CHAT_HISTORY[chat_id] = [entry]


def clear_chat_history(chat_id):
    CHAT_HISTORY[chat_id] = []


def show_chat_history(chat_id=None):
    if chat_id == None:
        return CHAT_HISTORY
    else:
        return CHAT_HISTORY[chat_id]


def set_user_system_prompt(chat_id, prompt):
    USER_SYSTEM_PROMPTS[chat_id] = prompt.lstrip("/new_prompt")


def show_user_system_prompt(chat_id):
    if USER_SYSTEM_PROMPTS.get(chat_id):
        return f"Here is the current user system prompt: {USER_SYSTEM_PROMPTS.get(chat_id)}"
    else:
        return f"No user system prompt. Default system prompt is used: {inf_manager.get_default_sys_prompt()}"


@bot.message_handler(commands=['start', 'lang'])
def start(message):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    item1 = telebot.types.KeyboardButton("Chat in English")
    item2 = telebot.types.KeyboardButton("Parler en français")
    item3 = telebot.types.KeyboardButton("Говорить по-русски")
    markup.add(item1, item2, item3)

    bot.send_message(message.chat.id, "Select your preferred language, please.", reply_markup=markup)

# Button EN
@bot.message_handler(func=lambda message: message.text == "Chat in English")
def button1(message):
    set_lang("EN", message.chat.id)
    bot.send_message(message.chat.id, "OK, we'll continue in English.")

# Button FR
@bot.message_handler(func=lambda message: message.text == "Parler en français")
def button2(message):
    set_lang("FR", message.chat.id)
    bot.send_message(message.chat.id, "D'accord, on va continuer en français.")

# Button RU
@bot.message_handler(func=lambda message: message.text == "Говорить по-русски")
def button3(message):
    set_lang("FR", message.chat.id)
    bot.send_message(message.chat.id, "Хорошо, мы продолжим говорить по-русски.")



# Special commands handler
@bot.message_handler(regexp=r"\/[a-z\_]+", content_types=['text'])
def command_handle_special(message):
    chat_id = message.chat.id
    cmd = message.text
    
    try:
        if "/new_prompt" in cmd:
            set_user_system_prompt(chat_id, cmd)
            bot.send_message(chat_id, "Your system prompt has been updated")
        elif cmd == "/current_prompt":
            bot.send_message(chat_id, show_user_system_prompt(chat_id))
        elif cmd == "/clean_history":
            clear_chat_history(chat_id)
            bot.send_message(chat_id, f"Conversation history cleared: {show_chat_history(chat_id)}")
        elif cmd == "/chat_history":
            bot.send_message(chat_id, "Current conversation history:")
            for i in show_chat_history(chat_id):
                bot.send_message(chat_id, f"Round: {i}")
        elif cmd == "/full_chat_history":
            bot.send_message(chat_id, f"All conversation histories: {show_chat_history()}")
        elif cmd == "/help":
            bot.send_message(chat_id, HELP_MESSAGE)
        else:
            bot.send_message(chat_id, "Unknown command. Use /help for available commands.")
    except Exception as e:
        bot.send_message(chat_id, f"Error processing command: {e}")

# First general handler of messages
@bot.message_handler(content_types=['text'])
def command_handle_text(message):
    try:
        chat_id = message.chat.id
        msg = message.text
        if USER_SYSTEM_PROMPTS.get(message.chat.id):
            reply_and_remember(chat_id=chat_id, user_system_prompt=USER_SYSTEM_PROMPTS.get(message.chat.id), qr=msg)
        else:
            reply_and_remember(chat_id=chat_id, qr=msg)
    except Exception as e:
        bot.send_message(message.chat.id, f"An error occurred: {e}")
        clear_chat_history(message.chat.id)
        return traceback.print_exc()


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
        if text:
            # Split text into chunks of 4096 characters (Telegram's message limit)
            chunks = [text[i:i+3800] for i in range(0, len(text), 3800)]
            for chunk in chunks:
                extracted_entry = (chunk, "Thank you for the provided context. You can now ask me questions about it.")
                add_to_chat_history(
                    chat_id=message.chat.id,
                    entry=extracted_entry
                )
        else:
            bot.send_message(message.chat.id, "No text could be extracted from the PDF.")
        
        # msg = message.caption
        # query = f"{msg}\n{file_name}\n{text}"
        # chat_id = message.chat.id
        # reply_and_remember(chat_id=chat_id, infer_type=INFER_MODE, qr=query)
    except Exception:
        bot.send_message(message.chat.id, "File could not be processed.")
        return traceback.print_exc() 



bot.polling(none_stop=True, interval=0)
