import requests
import configparser
import logging

# Konfigurasi logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Membaca konfigurasi
config = configparser.ConfigParser()
if not config.read('config.ini'):
    logging.error("File config.ini tidak ditemukan.")
    raise FileNotFoundError("File config.ini tidak ditemukan. Pastikan file ada di direktori yang sama.")

try:
    telegram_bot_token = config['telegram']['bottoken']
    telegram_chat_id = config['telegram']['chatid']
except KeyError as e:
    logging.error(f"Konfigurasi tidak lengkap di config.ini: {e}")
    raise Exception(f"Pastikan file config.ini memiliki bagian [telegram] dengan 'bottoken' dan 'chatid'.")

# Validasi dasar
if not telegram_bot_token or not telegram_chat_id:
    logging.error("Token bot atau chat ID kosong di config.ini.")
    raise ValueError("Token bot dan chat ID tidak boleh kosong.")
if not telegram_bot_token.startswith("bot") and ":" not in telegram_bot_token:
    logging.warning("Format token bot mungkin tidak valid.")

def telegram_send_message(message: str, chat_id: str = telegram_chat_id) -> bool:
    """
    Mengirim pesan ke Telegram.
    
    :param message: Pesan yang akan dikirim.
    :param chat_id: ID chat tujuan (default dari config).
    :return: True jika berhasil, False jika gagal.
    """
    api_url = f"https://api.telegram.org/bot{telegram_bot_token}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': message,
        'parse_mode': 'html',
        'disable_web_page_preview': True
    }
    
    try:
        logging.debug(f"Mengirim pesan ke chat {chat_id}: {message[:50]}...")
        response = requests.post(api_url, json=payload, timeout=10)
        response.raise_for_status()
        logging.info(f"Pesan berhasil dikirim ke chat {chat_id}.")
        return True
    
    except requests.exceptions.RequestException as e:
        logging.error(f"Gagal mengirim pesan ke chat {chat_id}: {e}")
        logging.debug(f"Response: {response.text if 'response' in locals() else 'No response'}")
        return False
