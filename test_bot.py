import logging
import requests
import datetime
import io
import pandas as pd
from telegram import __version__ as TG_VER

try:
    from telegram import __version_info__
except ImportError:
    __version_info__ = (0, 0, 0, 0, 0)  # type: ignore[assignment]

if __version_info__ < (20, 0, 0, "alpha", 1):
    raise RuntimeError(
        f"This example is not compatible with your current PTB version {TG_VER}. To view the "
        f"{TG_VER} version of this example, "
        f"visit https://docs.python-telegram-bot.org/en/v{TG_VER}/examples.html"
    )
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler

# Define key
TOKEN = "6445050105:AAGaFyxd5d0Mp-_kUfQOhAg7ZFhnQv53IXU"
BASE_URL = "https://api.binance.com/api/v3"

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

# Define main code


def get_symbol_data(symbol):
    url = f"{BASE_URL}/klines"
    params = {
        "symbol": symbol,
        "interval": "1h",
        "limit": 1
    }
    response = requests.get(url, params=params)
    data = response.json()
    columns = [
        "Kline open time",
        "Open price",
        "High price",
        "Low price",
        "Close price",
        "Volume",
        "Kline Close time",
        "Quote asset volume",
        "Number of trades",
        "Taker buy base asset volume",
        "Taker buy quote asset volume",
        "Unused field"
    ]
    df = pd.DataFrame(data, columns=columns)
    return df


def get_usdt_trading_pairs():
    response = requests.get("https://api.binance.com/api/v3/exchangeInfo")
    data = response.json()

    usdt_pairs = []

    for symbol_info in data['symbols']:
        if symbol_info['quoteAsset'] == 'USDT':
            usdt_pairs.append(symbol_info['symbol'])

    return usdt_pairs

# get MA20 volume


def get_ma20_volume(symbol):
    url = f"{BASE_URL}/klines"
    params = {
        "symbol": symbol,
        "interval": "1h",
        "limit": 20
    }
    response = requests.get(url, params=params)
    data = response.json()
    volumes = [float(entry[5]) for entry in data]
    ma20_volume = sum(volumes) / len(volumes)
    return ma20_volume

# Inline keyboard


async def send_chart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("Sending chart...")
    query = update.callback_query
    await query.answer()
    symbol = f"BINANCE:{query.data}"
    # Get chart image using CHART-IMG API
    chart_api_key = "esFwC38dqg3anwgXuhbaB8UeGt2YWKHW7Lx1nm6Q"
    chart_url = "https://api.chart-img.com/v2/tradingview/advanced-chart"
    headers = {
        "x-api-key": chart_api_key,
        "content-type": "application/json"
    }
    chart_payload = {
        "theme": "dark",
        "interval": "1h",
        "symbol": symbol,
        "override": {
            "showStudyLastValue": True
        },
        "studies": [
            {
                "name": "Volume",
                "forceOverlay": False
            },
            {
                "name": "Ichimoku Cloud",
                "input": {
                    "in_0": 9,
                    "in_1": 26,
                    "in_2": 52,
                    "in_3": 26
                },
                "override": {
                    "ConversionLine.visible": True,
                    "ConversionLine.linewidth": 1,
                    "ConversionLine.plottype": "line",
                    "ConversionLine.color": "rgb(33,150,243)",
                    "BaseLine.visible": True,
                    "BaseLine.linewidth": 1,
                    "BaseLine.plottype": "line",
                    "BaseLine.color": "rgb(128,25,34)",
                    "LaggingSpan.visible": True,
                    "LaggingSpan.linewidth": 1,
                    "LaggingSpan.plottype": "line",
                    "LaggingSpan.color": "rgb(67,160,71)",
                    "LeadingSpanA.visible": True,
                    "LeadingSpanA.linewidth": 1,
                    "LeadingSpanA.plottype": "line",
                    "LeadingSpanA.color": "rgb(165,214,167)",
                    "LeadingSpanB.visible": True,
                    "LeadingSpanB.linewidth": 1,
                    "LeadingSpanB.plottype": "line",
                    "LeadingSpanB.color": "rgb(250,161,164)",
                    "Plots Background.visible": True,
                    "Plots Background.transparency": 90
                }
            }
        ]
    }
    chart_response = requests.post(
        chart_url, headers=headers, json=chart_payload)
    image_buffer = io.BytesIO(chart_response.content)
    await update.effective_message.reply_photo(photo=image_buffer, caption=query.data)


# Check trading conditions and send message to Telegram
tokens_to_check = ["BTCUSDT", "UNIUSDT", "MAVUSDT", "OPUSDT", "UNFIUSDT", "DOGEUSDT",
                   "SUIUSDT", "BAKEUSDT", "AUDIOUSDT", "GRTUSDT", "LITUSDT", "BELUSDT", "RENUSDT", "LINKUSDT"]

# Funtion in JobQueue


def time_to_next_hour(target_minute, current_time=None):
    current_time = datetime.datetime.now()
    next_hour = current_time.replace(
        minute=0, second=0, microsecond=0) + datetime.timedelta(minutes=target_minute)
    time_to_wait = (next_hour - current_time).total_seconds()
    return round(time_to_wait)


def remove_job_if_exists(name: str, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Remove job with given name. Returns whether job was removed."""
    current_jobs = context.job_queue.get_jobs_by_name(name)
    if not current_jobs:
        return False
    for job in current_jobs:
        job.schedule_removal()
    return True


async def stop_checking(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("Stopping bot...")
    chat_id = update.effective_message.chat_id
    job_removed = remove_job_if_exists(str(chat_id), context)
    text = "Checking stopped!" if job_removed else "You have no active checking."
    await update.effective_message.reply_text(text)


async def start_checking(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("Starting bot...")
    chat_id = update.effective_message.chat_id
    try:
        job_removed = remove_job_if_exists(str(chat_id), context)
        target_minute = 50
        current_time = datetime.datetime.now()
        time_to_wait = time_to_next_hour(target_minute, current_time)
        if time_to_wait < 0:
            time_to_wait += 3600
        context.job_queue.run_repeating(
            check_conditions_and_send_message, interval=3600, first=time_to_wait, chat_id=chat_id, name=str(chat_id))

        text = "Checking conditions every hour..."
        await update.effective_message.reply_text(f"{text} Time to wait: {time_to_wait} seconds")
    except (IndexError, ValueError):
        await update.effective_message.reply_text("Usage: /start_checking")


async def check_conditions_and_send_message(context: ContextTypes.DEFAULT_TYPE):
    print("Checking conditions...")
    job = context.job
    for symbol in tokens_to_check:
        symbol_data = get_symbol_data(symbol)
        current_price = float(symbol_data['Close price'])
        open_price = float(symbol_data["Open price"])
        current_volume = float(symbol_data["Volume"])
        ma20_volume = get_ma20_volume(symbol)

        if current_price > open_price and current_volume > ma20_volume:
            keyboard = [[InlineKeyboardButton(
                text=f"View Chart {symbol}", callback_data=symbol)]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            message = f"🚀BUY SIGNAL {symbol} 📈\n💸Price: {current_price}\nOpen Price: {open_price}\nVolume: {current_volume}\nMA20 Volume: {ma20_volume}"
            await context.bot.send_message(job.chat_id, text=message, reply_markup=reply_markup)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends explanation on how to use the bot."""
    await update.message.reply_text("Bào sàn binance nè\n /start_checking để bắt đầu theo dõi \n /stop_checking để dừng \n /listtoken để xem danh sách token \n /addtoken để thêm token \n /removetoken để xóa token")


async def return_list_token(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends explanation on how to use the bot."""
    await update.message.reply_text(tokens_to_check)


async def add_token(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Extract the argument and convert to uppercase
    try:
        new_token = context.args[0].upper()
        tokens_to_check.append(new_token)
        await update.message.reply_text(text=f"Added {new_token} to the list.")
    except (IndexError, ValueError):
        await update.message.reply_text("Usage: /addtoken <token>")


async def remove_token(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Extract the argument and convert to uppercase
    try:
        new_token = context.args[0].upper()
        tokens_to_check.remove(new_token)
        await update.message.reply_text(
            text=f"Removed {new_token} from the list.")
    except (IndexError, ValueError):
        await update.message.reply_text("Usage: /removetoken <token>")


def main() -> None:
    """Run bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(TOKEN).build()

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler(["start", "help"], start))
    application.add_handler(CommandHandler("start_checking", start_checking))
    application.add_handler(CommandHandler("listtoken", return_list_token))
    application.add_handler(CommandHandler("addtoken", add_token))
    application.add_handler(CommandHandler("removetoken", remove_token))
    application.add_handler(CommandHandler(
        "stop_checking", stop_checking))
    application.add_handler(CallbackQueryHandler(send_chart))

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
