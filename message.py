import requests
import configparser

# Membaca konfigurasi dari file config.ini
config = configparser.ConfigParser()
config.read('config.ini')

try:
    telegram_bot_token = config['telegram']['bottoken']
    telegram_chat_id = config['telegram']['chatid']
except KeyError:
    raise Exception("Pastikan file config.ini sudah diisi dengan token bot dan chat ID Telegram.")

def telegram_send_message(message):
    """
    Mengirim pesan ke Telegram.
    
    :param message: Pesan yang akan dikirim.
    """
    api_url = f"https://api.telegram.org/bot{telegram_bot_token}/sendMessage"
    try:
        response = requests.post(api_url, json={
            'chat_id': telegram_chat_id,
            'text': message,
            'parse_mode': 'html',
            'disable_web_page_preview': True
        })
        print(response.text)
    except Exception as e:
        print(f"Error sending message to Telegram: {e}")
