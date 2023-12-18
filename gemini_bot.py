from os import environ
import telebot

import google.generativeai as genai
from telebot import TeleBot
from telebot.types import Message

GOOGLE_GEMINI_KEY = environ.get("GOOGLE_GEMINI_KEY")
genai.configure(api_key=GOOGLE_GEMINI_KEY)
model = genai.GenerativeModel('gemini-pro')
BOT_USERNAME = environ.get("BOT_USERNAME")
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

def is_bot_mentioned(message):
    """检查消息中是否提及了机器人"""
    return f"@{BOT_USERNAME}" in message.text if message.text else False

def is_private_chat(message):
    """检查是否为单聊"""
    return message.chat.type == "private"

def is_group_chat(message):
    """检查是否为群聊"""
    return message.chat.type in ["group", "supergroup"]

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
	bot.reply_to(message, "Hi, I'm Gemini, just ask me anything!")

@bot.message_handler(func=lambda message: is_private_chat(message) and is_user_allowed(message))
def echo_all(message):
    print(message.text)
    response = model.generate_content(message.text)
    print(response.text)
    bot.reply_to(message, process_text_with_code(response.text), parse_mode="MarkdownV2")

@bot.message_handler(func=lambda message: 
                     is_group_chat(message) and 
                     is_user_allowed(message) and 
                     (is_bot_mentioned(message) or message.reply_to_message))
def echo_all_group(message):
    print(message.from_user.id)
    print(message.chat.id)
    print(message.text)
    # model = genai.GenerativeModel('gemini-pro')
    message_text = message.text.replace(f"@{BOT_USERNAME}", "").strip()
    response = model.generate_content(message_text)
    print(response.text)
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