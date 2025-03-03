import pandas as pd
import time
import json
import datetime
import logging
import sys
from misc import get_header, get_json
from datetime import timedelta
from message import telegram_send_message
from hyperliquid import get_position, get_leaderboard_base_info, get_markprice

# Konfigurasi logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)

# Load user addresses dari file JSON
def load_user_addresses():
    try:
        with open('user_addresses.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logging.error("File user_addresses.json tidak ditemukan. Jalankan setup.py terlebih dahulu.")
        sys.exit(1)
    except json.JSONDecodeError:
        logging.error("Format user_addresses.json tidak valid.")
        sys.exit(1)

TARGETED_USER_ADDRESSES = load_user_addresses()

ACCOUNT_INFO_URL_TEMPLATE = 'https://hyperdash.info/trader/{}'

# Fungsi untuk memotong alamat pengguna
def shorten_address(user_address):
    """
    Memotong alamat pengguna untuk menampilkan hanya 5 karakter pertama setelah '0x'.
    
    :param user_address: Alamat pengguna lengkap (misalnya, "0x5d2f4460ac3514ada79f5d9838916e508ab39bb7").
    :return: Alamat yang dipendekkan (misalnya, "0x5d2f4").
    """
    if user_address.startswith("0x") and len(user_address) > 7:
        return user_address[:7]  # Ambil 5 karakter setelah '0x'
    return user_address  # Jika format tidak sesuai, kembalikan alamat asli

# Modifying DataFrame, including calculating estimated entry size in USDT
def modify_data(data) -> pd.DataFrame:
    """
    Memproses data posisi trading dari API Hyperliquid.
    
    Parameters:
        data (dict): Data mentah dari API Hyperliquid.
    
    Returns:
        pd.DataFrame: DataFrame yang berisi posisi trading yang diproses.
    """
    if not data or 'positions' not in data:
        logging.warning("Invalid data structure received from API.")
        return pd.DataFrame()

    positions = data['positions']
    df = pd.DataFrame(positions)

    # Debugging: Cetak kolom yang tersedia
    logging.info(f"Available columns in DataFrame: {df.columns.tolist()}")

    # Pastikan kolom 'coin' ada di DataFrame
    if 'coin' not in df.columns:
        logging.error("Column 'coin' not found in DataFrame.")
        return pd.DataFrame()

    # Set 'coin' sebagai index
    df.set_index('coin', inplace=True)

    # Menghitung estimatedEntrySize
    df['estimatedEntrySize'] = round((abs(df['size']) / df['leverage']) * df['entry_price'], 2)

    # Menentukan posisi (LONG/SHORT)
    df['estimatedPosition'] = df['size'].apply(lambda x: 'LONG' if x > 0 else 'SHORT')

    # Memformat waktu update (UTC+7)
    df['updateTime'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # Memilih kolom yang diperlukan
    position_result = df[['estimatedPosition', 'leverage', 'estimatedEntrySize', 
                          'entry_price', 'position_value', 'unrealized_pnl', 'updateTime']]
    return position_result

previous_symbols = {}
previous_position_results = {}
is_first_runs = {address: True for address in TARGETED_USER_ADDRESSES}

# Function to send new position message
def send_new_position_message(symbol, row, user_address):
    """
    Mengirim pesan Telegram ketika posisi baru dibuka.
    
    Parameters:
        symbol (str): Simbol trading (misalnya, BTC).
        row (pd.Series): Baris DataFrame yang berisi detail posisi.
        user_address (str): Alamat pengguna.
    """
    short_address = shorten_address(user_address)  # Potong alamat
    estimated_position = row['estimatedPosition']
    leverage = row['leverage']
    estimated_entry_size = row['estimatedEntrySize']
    entry_price = row['entry_price']
    pnl = row['unrealized_pnl']
    updatetime = row['updateTime']
    pnl_emoji = "🟢" if pnl >= 0 else "🔴"  # Emoji untuk PnL positif/negatif
    message = (
        f"⚠️ [<b>{short_address}</b>]\n"
        f"❇️ <b>New position opened</b>\n\n"
        f"<b>Position:</b> {symbol} {estimated_position} {leverage}X\n\n"
        f"💵 Base currency - USDT\n"
        f"------------------------------\n"
        f"🎯 <b>Entry Price:</b> {entry_price}\n"
        f"💰 <b>Est. Entry Size:</b> {estimated_entry_size}\n"
        f"{pnl_emoji} <b>PnL:</b> {pnl}\n\n"
        f"<b>Last Update:</b>\n{updatetime} (UTC+7)\n"
        f"<a href='{ACCOUNT_INFO_URL_TEMPLATE.format(user_address)}'><b>VIEW PROFILE ON HYPERDASH</b></a>"
    )
    telegram_send_message(message)

# Function to send closed position message
def send_closed_position_message(symbol, row, user_address):
    """
    Mengirim pesan Telegram ketika posisi ditutup.
    
    Parameters:
        symbol (str): Simbol trading.
        row (pd.Series): Baris DataFrame yang berisi detail posisi.
        user_address (str): Alamat pengguna.
    """
    short_address = shorten_address(user_address)  # Potong alamat
    estimated_position = row['estimatedPosition']
    leverage = row['leverage']
    updatetime = row['updateTime']
    message = (
        f"⚠️ [<b>{short_address}</b>]\n"
        f"⛔️ <b>Position closed</b>\n\n"
        f"<b>Position:</b> {symbol} {estimated_position} {leverage}X\n"
        f"💵 <b>Current Price:</b> {get_markprice(symbol)} USDT\n\n"
        f"<b>Last Update:</b>\n{updatetime} (UTC+7)\n"
        f"<a href='{ACCOUNT_INFO_URL_TEMPLATE.format(user_address)}'><b>VIEW PROFILE ON HYPERDASH</b></a>"
    )
    telegram_send_message(message)

# Function to send current positions
def send_current_positions(position_result, user_address):
    """
    Mengirim pesan Telegram dengan daftar posisi saat ini.
    
    Parameters:
        position_result (pd.DataFrame): DataFrame yang berisi posisi saat ini.
        user_address (str): Alamat pengguna.
    """
    short_address = shorten_address(user_address)  # Potong alamat
    if position_result.empty:
        telegram_send_message(f"⚠️ [<b>{short_address}</b>]\n💎 <b>No positions found</b>")
    else:
        telegram_send_message(f"⚠️ [<b>{short_address}</b>]\n💎 <b>Current positions:</b>")
        for symbol, row in position_result.iterrows():
            estimated_position = row['estimatedPosition']
            leverage = row['leverage']
            estimated_entry_size = row['estimatedEntrySize']
            entry_price = row['entry_price']
            pnl = row['unrealized_pnl']
            updatetime = row['updateTime']
            pnl_emoji = "🟢" if pnl >= 0 else "🔴"  # Emoji untuk PnL positif/negatif
            message = (
                f"<b>Position:</b> {symbol} {estimated_position} {leverage}X\n\n"
                f"Base currency - USDT\n"
                f"------------------------------\n"
                f"🎯 <b>Entry Price:</b> {entry_price}\n"
                f"💰 <b>Est. Entry Size:</b> {estimated_entry_size}\n"
                f"{pnl_emoji} <b>PnL:</b> {pnl}\n\n"
                f"<b>Last Update:</b>\n{updatetime} (UTC+7)\n"
                f"<a href='{ACCOUNT_INFO_URL_TEMPLATE.format(user_address)}'><b>VIEW PROFILE ON HYPERDASH</b></a>"
            )
            telegram_send_message(message)

while True:
    try:
        start_time = time.time()  # Catat waktu mulai iterasi
        
        for user_address in TARGETED_USER_ADDRESSES:
            ACCOUNT_INFO_URL = ACCOUNT_INFO_URL_TEMPLATE.format(user_address)
            leaderboard_info = get_leaderboard_base_info(user_address)

            if isinstance(leaderboard_info, str):  # Jika terjadi error
                logging.error(f"Error untuk alamat {user_address}: {leaderboard_info}")
                telegram_send_message(f"Error untuk alamat {user_address}: {leaderboard_info}")
                continue

            position_result = modify_data(leaderboard_info)

            new_symbols = position_result.index.difference(previous_symbols.get(user_address, pd.Index([])))
            if not is_first_runs[user_address] and not new_symbols.empty:
                for symbol in new_symbols:
                    send_new_position_message(symbol, position_result.loc[symbol], user_address)

            closed_symbols = previous_symbols.get(user_address, pd.Index([])).difference(position_result.index)
            if not is_first_runs[user_address] and not closed_symbols.empty:
                for symbol in closed_symbols:
                    if symbol in previous_position_results.get(user_address, pd.DataFrame()).index:
                        send_closed_position_message(symbol, previous_position_results[user_address].loc[symbol], user_address)

            if is_first_runs[user_address]:
                send_current_positions(position_result, user_address)

            previous_position_results[user_address] = position_result.copy()
            previous_symbols[user_address] = position_result.index.copy()
            is_first_runs[user_address] = False

        # Hitung waktu eksekusi dan log
        ping_time = (time.time() - start_time) * 1000  # Konversi ke milidetik
        current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        logging.info(f"✅ Bot is still running | Time: {current_time} | Ping: {ping_time:.2f}ms")
        
        time.sleep(60)  # Tunggu 60 detik sebelum iterasi berikutnya
        
    except Exception as e:
        logging.error(f"Error occurred: {e}")
        message = f"Error occurred for address <b>{user_address}</b>:\n{e}\n\n" \
                  f"Retrying after 60s"
        telegram_send_message(message)
        time.sleep(60)
