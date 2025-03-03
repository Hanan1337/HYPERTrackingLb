import pandas as pd
import time
import datetime
import logging
import sys
import threading
from misc import get_header, get_json
from datetime import timedelta
from message import telegram_send_message, process_telegram_updates, load_user_addresses
from hyperliquid import get_position, get_leaderboard_base_info, get_markprice
from shared import TARGETED_USER_ADDRESSES, user_addresses_lock

# Konfigurasi logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)

# Inisialisasi TARGETED_USER_ADDRESSES saat startup
TARGETED_USER_ADDRESSES.extend(load_user_addresses())

ACCOUNT_INFO_URL_TEMPLATE = 'https://hyperdash.info/trader/{}'

def shorten_address(user_address):
    if user_address.startswith("0x") and len(user_address) > 7:
        return user_address[:7]
    return user_address

def modify_data(data) -> pd.DataFrame:
    if not data or 'positions' not in data:
        logging.warning("Invalid data structure received from API.")
        return pd.DataFrame()

    positions = data['positions']
    df = pd.DataFrame(positions)
    
    required_columns = ['coin', 'size', 'leverage', 'entry_price', 'position_value', 'unrealized_pnl']
    missing_cols = [col for col in required_columns if col not in df.columns]
    if missing_cols:
        logging.error(f"Missing required columns: {missing_cols}")
        return pd.DataFrame()

    df.set_index('coin', inplace=True)
    df['estimatedEntrySize'] = df.apply(
        lambda row: round((abs(row['size']) / row['leverage']) * row['entry_price'], 2) 
        if row['leverage'] != 0 else 0, axis=1
    )
    df['estimatedPosition'] = df['size'].apply(lambda x: 'LONG' if x > 0 else 'SHORT')
    df['updateTime'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    return df[['estimatedPosition', 'leverage', 'estimatedEntrySize', 
              'entry_price', 'position_value', 'unrealized_pnl', 'updateTime']]

previous_symbols = {}
previous_position_results = {}
is_first_runs = {}

def send_new_position_message(symbol, row, user_address):
    short_address = shorten_address(user_address)
    estimated_position = row['estimatedPosition']
    leverage = row['leverage']
    estimated_entry_size = row['estimatedEntrySize']
    entry_price = row['entry_price']
    pnl = row['unrealized_pnl']
    updatetime = row['updateTime']
    pnl_emoji = "🟢" if pnl >= 0 else "🔴"
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

def send_closed_position_message(symbol, row, user_address):
    short_address = shorten_address(user_address)
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

def send_current_positions(position_result, user_address):
    short_address = shorten_address(user_address)
    if position_result.empty:
        telegram_send_message(f"⚠️ [<b>{short_address}</b>]\n💎 <b>No positions found</b>")
    else:
        message = f"⚠️ [<b>{short_address}</b>]\n💎 <b>Current positions:</b>\n\n"
        for symbol, row in position_result.iterrows():
            pnl_emoji = "🟢" if row['unrealized_pnl'] >= 0 else "🔴"
            message += (
                f"<b>{symbol}</b> {row['estimatedPosition']} {row['leverage']}X\n"
                f"🎯 Entry: {row['entry_price']} | 💰 Size: {row['estimatedEntrySize']}\n"
                f"{pnl_emoji} PnL: {row['unrealized_pnl']}\n"
                f"------------------------------\n"
            )
        message += f"<b>Last Update:</b> {row['updateTime']} (UTC+7)\n"
        message += f"<a href='{ACCOUNT_INFO_URL_TEMPLATE.format(user_address)}'><b>VIEW PROFILE</b></a>"
        telegram_send_message(message)

def telegram_polling():
    global offset
    while True:
        try:
            offset = process_telegram_updates(offset)
            time.sleep(1)
        except Exception as e:
            logging.error(f"Error di thread Telegram polling: {e}")
            time.sleep(10)

def monitor_positions():
    while True:
        try:
            start_time = time.time()
            
            with user_addresses_lock:
                current_addresses = TARGETED_USER_ADDRESSES.copy()

            for address in current_addresses:
                if address not in is_first_runs:
                    is_first_runs[address] = True

            for user_address in current_addresses:
                ACCOUNT_INFO_URL = ACCOUNT_INFO_URL_TEMPLATE.format(user_address)
                leaderboard_info = get_leaderboard_base_info(user_address)

                if isinstance(leaderboard_info, str):
                    logging.error(f"Error untuk alamat {user_address}: {leaderboard_info}")
                    telegram_send_message(f"Error untuk alamat {user_address}: {leaderboard_info}", telegram_chat_id)
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

            ping_time = (time.time() - start_time) * 1000
            current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            logging.info(f"✅ Bot is still running | Time: {current_time} | Ping: {ping_time:.2f}ms")
            
            time.sleep(60)
        
        except Exception as e:
            logging.error(f"Global error occurred: {e}")
            error_message = f"Global error occurred:\n{e}\n\nRetrying after 60s"
            telegram_send_message(error_message, telegram_chat_id)
            time.sleep(60)

# Jalankan thread untuk polling Telegram
offset = None
telegram_thread = threading.Thread(target=telegram_polling, daemon=True)
telegram_thread.start()

# Jalankan loop utama untuk pemantauan posisi
monitor_positions()
