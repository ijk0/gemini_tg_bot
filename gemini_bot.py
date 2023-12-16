from os import environ
import telebot

import google.generativeai as genai
from telebot import TeleBot
from telebot.types import Message

GOOGLE_GEMINI_KEY = environ.get("GOOGLE_GEMINI_KEY")
genai.configure(api_key=GOOGLE_GEMINI_KEY)

botToken = environ.get("BOT_TOKEN")

WHITELISTED_USERS = environ.get('WHITELISTED_USERS', '').split(',')
WHITELISTED_GROUPS = environ.get('WHITELISTED_GROUPS', '').split(',')

bot = telebot.TeleBot(botToken)

def is_user_allowed(message):
    """检查用户或群组是否在白名单中"""
    user_id = message.from_user.id
    chat_id = message.chat.id
    str_user_id = str(user_id)
    str_chat_id = str(chat_id)
    return str_user_id in WHITELISTED_USERS or str_chat_id in WHITELISTED_GROUPS

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
	bot.reply_to(message, "I'm Gemini, just ask me anything?")

@bot.message_handler(func=lambda message: is_user_allowed(message))
def echo_all(message):
	# print(message.text)
	model = genai.GenerativeModel('gemini-pro')
	response = model.generate_content(message.text)
	# print(response.text)
	bot.reply_to(message, process_text_with_code(response.text), parse_mode="MarkdownV2")
	
@bot.message_handler(func=lambda message: not is_user_allowed(message))
def handle_unauthorized_messages(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    if chat_id < 0:  # 群组 ID 为负数
        response = f"Unauthorized access attempt in Group ID: {chat_id}. Sorry, you are not authorized to use this bot."
    else:
        response = f"Unauthorized access attempt by User ID: {user_id}. Sorry, you are not authorized to use this bot."
    
    bot.reply_to(message, response)


def escape_markdown_v2(text):
    escape_chars = '_*[]()~`>#+-=|{}.!'
    return ''.join('\\' + char if char in escape_chars else char for char in text)

def process_text_with_code(text):
    parts = text.split("```")  # 假设使用 ``` 分隔代码块
    for i in range(len(parts)):
        if i % 2 == 0:
            # 转义普通文本
            parts[i] = escape_markdown_v2(parts[i])
        else:
            # 保持代码块原样，但添加 ``` 用于 Markdown
            parts[i] = "```" + parts[i] + "```"
    return "".join(parts)

bot.infinity_polling()