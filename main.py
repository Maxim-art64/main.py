import os
import requests
from datetime import datetime, timedelta
from telegram import Bot, Update
from telegram.ext import Updater, CommandHandler, CallbackContext

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = int(os.getenv('CHAT_ID'))

BUY_THRESHOLD = -1.0
SELL_THRESHOLD = 1.0

def fetch_pairs():
    try:
        url = 'https://api.dexscreener.com/latest/dex/pairs/polygon'
        res = requests.get(url)
        return res.json().get('pairs', [])
    except Exception as e:
        print(f"Ошибка при получении пар: {e}")
        return []

def format_signal(pair, price, change, signal_type):
    now = datetime.now()
    buy_start = now
    buy_end = now + timedelta(minutes=2)
    sell_start = now + timedelta(minutes=10)
    sell_end = now + timedelta(minutes=18)

    base = pair['baseToken']['symbol']
    dex = pair['dexId'].capitalize()
    url = pair.get('url', 'https://dexscreener.com')
    profit = abs(change) * 5 if signal_type == 'BUY' else change
    sell_price = price * (1 + profit / 100)
    risk = '🟢 Low' if abs(change) < 1.2 else '🟡 Medium' if abs(change) < 2.5 else '🔴 High'

    return (
        f"⚡️ TRADE SIGNAL\n\n"
        f"🔄 Пара: USDT ➡️ {base}\n"
        f"💱 Биржа: {dex} (Polygon)\n"
        f"📉 Цена покупки: {price:.6f} USDT\n"
        f"🕒 Время покупки: {buy_start.strftime('%H:%M')} — {buy_end.strftime('%H:%M')}\n\n"
        f"📈 Цель продажи: {sell_price:.6f} USDT\n"
        f"🕒 Время продажи: {sell_start.strftime('%H:%M')} — {sell_end.strftime('%H:%M')}\n"
        f"📊 Потенциал: ~{profit:.1f}%\n"
        f"🛡️ Риск: {risk}\n"
        f"🔗 Ссылка: {url}\n\n"
        f"📌 Рекомендация: {'Закупись в ближайшие 2 минуты!' if signal_type == 'BUY' else 'Подумай о фиксации прибыли.'}"
    )

def analyze_pair(pair):
    try:
        base = pair['baseToken']['symbol']
        quote = pair['quoteToken']['symbol']
        if quote != 'USDT':
            return None
        price = float(pair['priceUsd'])
        change_5m = float(pair['priceChange']['m5'])
        if change_5m <= BUY_THRESHOLD:
            return format_signal(pair, price, change_5m, 'BUY')
        elif change_5m >= SELL_THRESHOLD:
            return format_signal(pair, price, change_5m, 'SELL')
        else:
            return None
    except:
        return None

def check_signals():
    signals = []
    pairs = fetch_pairs()
    for pair in pairs:
        signal = analyze_pair(pair)
        if signal:
            signals.append(signal)
    return signals

def send_signals(context: CallbackContext):
    signals = check_signals()
    for msg in signals:
        try:
            context.bot.send_message(chat_id=CHAT_ID, text=msg)
        except Exception as e:
            print(f"Ошибка при отправке сообщения: {e}")

def check_command(update: Update, context: CallbackContext):
    signals = check_signals()
    if signals:
        for msg in signals:
            update.message.reply_text(msg)
    else:
        update.message.reply_text('Братиш, пока выгодных сделок нет.')

def main():
    updater = Updater(TELEGRAM_TOKEN, use_context=True)
    dispatcher = updater.dispatcher
    dispatcher.add_handler(CommandHandler('check', check_command))
    job_queue = updater.job_queue
    job_queue.run_repeating(send_signals, interval=180, first=10)
    updater.start_polling()
    print("Бот запущен!")
    updater.idle()

if __name__ == '__main__':
    main()
