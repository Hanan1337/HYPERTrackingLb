import json
import configparser

def setup():
    """
    Menyiapkan konfigurasi awal untuk bot.
    """
    # Setup Telegram
    config = configparser.ConfigParser()
    config['telegram'] = {}
    config['telegram']['bottoken'] = input("Masukkan token bot Telegram: ")
    config['telegram']['chatid'] = input("Masukkan chat ID Telegram: ")

    with open('config.ini', 'w') as configfile:
        config.write(configfile)

    # Setup user addresses
    user_addresses = []
    print("\nMasukkan alamat pengguna (tekan Enter setelah setiap alamat, kosongkan untuk selesai):")
    while True:
        address = input("Alamat pengguna: ").strip()
        if not address:
            break
        user_addresses.append(address)

    with open('user_addresses.json', 'w') as f:
        json.dump(user_addresses, f, indent=2)

    print("\nSetup selesai! File config.ini dan user_addresses.json telah dibuat.")

if __name__ == "__main__":
    setup()
