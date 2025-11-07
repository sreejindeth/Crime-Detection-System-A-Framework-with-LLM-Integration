
import os
import requests

bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
if not bot_token:
    print("Error: TELEGRAM_BOT_TOKEN environment variable is not set.")
    print("Please set it using: export TELEGRAM_BOT_TOKEN='your_token_here'")
    exit(1)

url = f"https://api.telegram.org/bot{bot_token}/getUpdates"

try:
    # Add timeout to prevent hanging
    response = requests.get(url, timeout=10)
    response.raise_for_status()  # Raise an exception for bad status codes
    data = response.json()
    
    # Check if 'result' key exists and is not empty
    if "result" in data and data["result"]:
        # Print the chat ID from the response
        for result in data["result"]:
            if "message" in result and "chat" in result["message"]:
                chat_id = result["message"]["chat"]["id"]
                print(f"Chat ID: {chat_id}")
            else:
                print("Warning: Message structure not found in result")
    else:
        print("No updates found. Send a message to your bot first.")
except requests.exceptions.Timeout:
    print("Error: Request timed out. Check your internet connection.")
except requests.exceptions.RequestException as e:
    print(f"Error: Failed to connect to Telegram API: {e}")
except KeyError as e:
    print(f"Error: Unexpected response format. Missing key: {e}")
except Exception as e:
    print(f"Error: {type(e).__name__}: {e}")
