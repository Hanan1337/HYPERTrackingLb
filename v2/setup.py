import json
import configparser
import logging

# Konfigurasi logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def setup():
    """
    Menyiapkan konfigurasi awal untuk bot.
    """
    logging.info("Memulai proses setup konfigurasi bot.")
    
    # Setup Telegram
    config = configparser.ConfigParser()
    config['telegram'] = {}
    
    while True:
        bottoken = input("Masukkan token bot Telegram: ").strip()
        if bottoken and ":" in bottoken:  # Validasi sederhana untuk format token
            break
        print("Token bot harus mengandung ':' dan tidak boleh kosong.")
        logging.warning("Input token bot tidak valid.")
    
    while True:
        chatid = input("Masukkan chat ID Telegram: ").strip()
        if chatid and chatid.lstrip('-').isdigit():  # Harus angka atau angka negatif
            break
        print("Chat ID harus berupa angka (bisa negatif) dan tidak boleh kosong.")
        logging.warning("Input chat ID tidak valid.")
    
    config['telegram']['bottoken'] = bottoken
    config['telegram']['chatid'] = chatid

    try:
        with open('config.ini', 'w') as configfile:
            config.write(configfile)
        logging.info("File config.ini telah dibuat.")
    except IOError as e:
        logging.error(f"Gagal menulis config.ini: {e}")
        raise

    # Setup user addresses
    user_addresses = []
    print("\nMasukkan alamat pengguna (tekan Enter setelah setiap alamat, kosongkan untuk selesai):")
    while True:
        address = input("Alamat pengguna: ").strip()
        if not address:
            break
        if address.startswith("0x") and len(address) == 42:  # Validasi alamat Ethereum
            user_addresses.append(address)
        else:
            print("Alamat harus diawali '0x' dan panjangnya 42 karakter.")
            logging.warning(f"Alamat tidak valid: {address}")
    
    try:
        with open('user_addresses.json', 'w') as f:
            json.dump(user_addresses, f, indent=2)
        logging.info(f"File user_addresses.json telah dibuat dengan {len(user_addresses)} alamat.")
    except IOError as e:
        logging.error(f"Gagal menulis user_addresses.json: {e}")
        raise

    print("\nSetup selesai! File config.ini dan user_addresses.json telah dibuat.")
    logging.info("Proses setup selesai.")

if __name__ == "__main__":
    setup()
