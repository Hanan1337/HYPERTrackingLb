import requests
import json

def get_markprice(symbol):
    """
    Mendapatkan harga mark (mark price) dari Hyperliquid API.
    
    :param symbol: Simbol trading (misalnya, BTC, ETH).
    :return: Harga mark atau pesan kesalahan jika gagal.
    """
    url = "https://api.hyperliquid.xyz/info"
    payload = {
        "type": "metaAndAssetCtxs"
    }
    headers = {
        'User-Agent': "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
        'Accept-Encoding': "gzip, deflate, br, zstd",
        'Content-Type': "application/json",
        'sec-ch-ua-platform': "\"Linux\"",
        'sec-ch-ua': "\"Chromium\";v=\"134\", \"Not:A-Brand\";v=\"24\", \"Brave\";v=\"134\"",
        'sec-ch-ua-mobile': "?0",
        'Sec-GPC': "1",
        'Accept-Language': "en-US,en;q=0.9",
        'Origin': "https://hyperdash.info",
        'Sec-Fetch-Site': "cross-site",
        'Sec-Fetch-Mode': "cors",
        'Sec-Fetch-Dest': "empty",
        'Referer': "https://hyperdash.info/"
    }

    try:
        response = requests.post(url, data=json.dumps(payload), headers=headers)
        response.raise_for_status()
        data = response.json()

        for asset in data[1]:  # Data mark price ada di indeks 1
            if 'markPx' in asset:
                if asset.get('name') == symbol:
                    return asset['markPx']

        return f"Symbol {symbol} not found in the response."

    except requests.exceptions.RequestException as e:
        return f"Error occurred while fetching mark price: {e}"

def get_position(user_address):
    """
    Mendapatkan posisi trading dari Hyperliquid API.
    
    :param user_address: Alamat pengguna (misalnya, "0x5d2f4460ac3514ada79f5d9838916e508ab39bb7").
    :return: Data posisi trading atau pesan kesalahan jika gagal.
    """
    url = "https://api.hyperliquid.xyz/info"
    payload = {
        "type": "clearinghouseState",
        "user": user_address
    }
    headers = {
        'User-Agent': "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
        'Accept-Encoding': "gzip, deflate, br, zstd",
        'Content-Type': "application/json",
        'sec-ch-ua-platform': "\"Linux\"",
        'sec-ch-ua': "\"Chromium\";v=\"134\", \"Not:A-Brand\";v=\"24\", \"Brave\";v=\"134\"",
        'sec-ch-ua-mobile': "?0",
        'Sec-GPC': "1",
        'Accept-Language': "en-US,en;q=0.9",
        'Origin': "https://hyperdash.info",
        'Sec-Fetch-Site': "cross-site",
        'Sec-Fetch-Mode': "cors",
        'Sec-Fetch-Dest': "empty",
        'Referer': "https://hyperdash.info/"
    }

    try:
        response = requests.post(url, data=json.dumps(payload), headers=headers)
        response.raise_for_status()
        data = response.json()

        positions = data.get("assetPositions", [])
        position_data = []

        for position in positions:
            pos_info = position.get("position", {})
            position_data.append({
                "coin": pos_info.get("coin", ""),
                "size": float(pos_info.get("szi", 0)),
                "entry_price": float(pos_info.get("entryPx", 0)),
                "position_value": float(pos_info.get("positionValue", 0)),
                "unrealized_pnl": float(pos_info.get("unrealizedPnl", 0)),
                "leverage": pos_info.get("leverage", {}).get("value", 0),
                "margin_used": float(pos_info.get("marginUsed", 0)),
                "liquidation_price": float(pos_info.get("liquidationPx", 0)),
                "max_leverage": pos_info.get("maxLeverage", 0),
                "cum_funding": pos_info.get("cumFunding", {})
            })

        return position_data

    except requests.exceptions.RequestException as e:
        return f"Error occurred while fetching positions: {e}"

def get_leaderboard_base_info(user_address):
    """
    Mendapatkan informasi dasar tentang trader dari Hyperliquid API berdasarkan alamat pengguna.
    
    :param user_address: Alamat pengguna (misalnya, "0x5d2f4460ac3514ada79f5d9838916e508ab39bb7").
    :return: Informasi dasar trader atau pesan kesalahan jika gagal.
    """
    import logging  # Pastikan logging diimpor di dalam file ini
    url = "https://api.hyperliquid.xyz/info"
    payload = {
        "type": "clearinghouseState",
        "user": user_address
    }
    headers = {
        'User-Agent': "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
        'Accept-Encoding': "gzip, deflate, br, zstd",
        'Content-Type': "application/json",
        'sec-ch-ua-platform': "\"Linux\"",
        'sec-ch-ua': "\"Chromium\";v=\"134\", \"Not:A-Brand\";v=\"24\", \"Brave\";v=\"134\"",
        'sec-ch-ua-mobile': "?0",
        'Sec-GPC': "1",
        'Accept-Language': "en-US,en;q=0.9",
        'Origin': "https://hyperdash.info",
        'Sec-Fetch-Site': "cross-site",
        'Sec-Fetch-Mode': "cors",
        'Sec-Fetch-Dest': "empty",
        'Referer': "https://hyperdash.info/"
    }

    try:
        logging.info(f"Fetching leaderboard data for {user_address}")
        response = requests.post(url, data=json.dumps(payload), headers=headers)
        response.raise_for_status()
        data = response.json()
        logging.debug(f"Raw API response for {user_address}: {data}")

        margin_summary = data.get("marginSummary", {})
        cross_margin_summary = data.get("crossMarginSummary", {})
        asset_positions = data.get("assetPositions", [])

        leaderboard_info = {
            "user_address": user_address,
            "profile_url": f"https://hyperdash.info/trader/{user_address}",
            "account_value": float(margin_summary.get("accountValue", 0) or 0),
            "total_notional_position": float(margin_summary.get("totalNtlPos", 0) or 0),
            "total_raw_usd": float(margin_summary.get("totalRawUsd", 0) or 0),
            "total_margin_used": float(margin_summary.get("totalMarginUsed", 0) or 0),
            "withdrawable": float(data.get("withdrawable", 0) or 0),
            "positions": []
        }

        for position in asset_positions:
            pos_info = position.get("position", {})
            logging.debug(f"Processing position for {user_address}: {pos_info}")
            position_data = {
                "coin": pos_info.get("coin", ""),
                "size": float(pos_info.get("szi", 0) or 0) if pos_info.get("szi") is not None else 0.0,
                "entry_price": float(pos_info.get("entryPx", 0) or 0) if pos_info.get("entryPx") is not None else 0.0,
                "position_value": float(pos_info.get("positionValue", 0) or 0) if pos_info.get("positionValue") is not None else 0.0,
                "unrealized_pnl": float(pos_info.get("unrealizedPnl", 0) or 0) if pos_info.get("unrealizedPnl") is not None else 0.0,
                "leverage": float(pos_info.get("leverage", {}).get("value", 0) or 0) if pos_info.get("leverage") is not None else 0.0,
                "margin_used": float(pos_info.get("marginUsed", 0) or 0) if pos_info.get("marginUsed") is not None else 0.0,
                "liquidation_price": float(pos_info.get("liquidationPx", 0) or 0) if pos_info.get("liquidationPx") is not None else 0.0,
                "max_leverage": float(pos_info.get("maxLeverage", 0) or 0) if pos_info.get("maxLeverage") is not None else 0.0,
                "cum_funding": pos_info.get("cumFunding", {})
            }
            leaderboard_info["positions"].append(position_data)

        logging.info(f"Successfully processed leaderboard info for {user_address}")
        return leaderboard_info

    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching leaderboard info for {user_address}: {e}")
        return f"Error occurred while fetching leaderboard info: {e}"
