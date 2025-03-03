def get_header():
    """
    Membuat header HTTP yang diperlukan untuk request ke API Hyperliquid.
    
    :return: Dictionary yang berisi header HTTP.
    """
    return {
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

def get_json(user_address):
    """
    Membuat payload JSON yang diperlukan untuk request ke API Hyperliquid.
    
    :param user_address: Alamat pengguna (misalnya, "0x5d2f4460ac3514ada79f5d9838916e508ab39bb7").
    :return: Dictionary yang berisi payload JSON.
    """
    return {
        "type": "clearinghouseState",
        "user": user_address
    }
