import requests


def send_telegram_message(token, chat_id, text):
    if not token or not chat_id:
        return False, "Telegram уведомления не настроены"
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    try:
        resp = requests.post(url, data={"chat_id": chat_id, "text": text})
        if resp.status_code != 200:
            return False, resp.text
        return True, ""
    except Exception as e:
        return False, str(e)
        return False, str(e)
