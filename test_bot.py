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
    params = {"symbol": symbol, "interval": "1h", "limit": 1}
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
        "Unused field",
    ]
    df = pd.DataFrame(data, columns=columns)
    df = df.round(2)
    return df


def get_usdt_trading_pairs():
    response = requests.get("https://api.binance.com/api/v3/exchangeInfo")
    data = response.json()

    usdt_pairs = []

    for symbol_info in data["symbols"]:
        if symbol_info["quoteAsset"] == "USDT":
            usdt_pairs.append(symbol_info["symbol"])

    return usdt_pairs


# Calculate RSI


def calculate_rsi(data, period=14):
    df = pd.DataFrame(data, columns=["Close"])

    df["Price Change"] = df["Close"].diff()

    df["Gain"] = df["Price Change"].apply(lambda x: x if x > 0 else 0)
    df["Loss"] = df["Price Change"].apply(lambda x: -x if x < 0 else 0)

    avg_gain = df["Gain"].rolling(window=period).mean()
    avg_loss = df["Loss"].rolling(window=period).mean()

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    current_rsi = rsi.iloc[-1]
    return current_rsi


def calculate_last_ma(data, length):
    if len(data) < length:
        return None

    last_ma = sum(data[-length:]) / length
    return round(last_ma, 2)


def calculate_ema(data, period):
    if len(data) < period:
        return None

    smoothing_factor = 2 / (period + 1)
    ema = data[-1]

    for i in range(len(data) - period, len(data)):
        ema = (data[i] - ema) * smoothing_factor + ema

    return ema


def calculate_ichimoku_cloud(data):
    if len(data) < 52:
        return None

    # Calculate Tenkan Sen (Conversion Line)
    tenkan_high = max(data[-9:])
    tenkan_low = min(data[-9:])
    tenkan_sen = (tenkan_high + tenkan_low) / 2

    # Calculate Kijun Sen (Base Line)
    kijun_high = max(data[-26:])
    kijun_low = min(data[-26:])
    kijun_sen = (kijun_high + kijun_low) / 2

    # Calculate Senkou Span A (Leading Span A)
    senkou_span_a = (tenkan_sen + kijun_sen) / 2

    # Calculate Senkou Span B (Leading Span B)
    kumo_high = max(data[-52:])
    kumo_low = min(data[-52:])
    senkou_span_b = (kumo_high + kumo_low) / 2

    return senkou_span_a, senkou_span_b


#! Get the symbol historical data


def get_symbol_history(symbol, limit=100):
    url = f"{BASE_URL}/klines"
    params = {"symbol": symbol, "interval": "1h", "limit": limit}
    response = requests.get(url, params=params)
    data = response.json()
    volumes = [float(entry[5]) for entry in data]
    closing_prices = [float(entry[4]) for entry in data]
    return volumes, closing_prices


#! Funtion return signal


def ma_crossover_signal(data):
    if len(data) < 8:
        return None

    ma5 = calculate_last_ma(data, 5)
    ma8 = calculate_last_ma(data, 8)

    if ma8 is None or ma5 is None:
        return None

    if ma5 > ma8:
        return True
    else:
        return False


def macd_crossover_signal(data):
    if len(data) < 26:
        return None

    ema_12 = calculate_ema(data, 12)
    ema_26 = calculate_ema(data, 26)

    if ema_12 is None or ema_26 is None:
        return None

    macd = ema_12 - ema_26
    if macd > 0:
        return True
    else:
        return False


def is_price_upper_cloud(data):
    ichimoku_cloud_data = calculate_ichimoku_cloud(data)

    if ichimoku_cloud_data is None:
        return None

    senkou_span_a, senkou_span_b = ichimoku_cloud_data

    if data[-1] > senkou_span_a and data[-1] > senkou_span_b:
        return True  # Price is upper the cloud
    else:
        return False  # Price is not upper the cloud


async def send_chart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("Sending chart...")
    query = update.callback_query
    await query.answer()
    symbol = f"BINANCE:{query.data}"
    # Get chart image using CHART-IMG API
    chart_api_key = "esFwC38dqg3anwgXuhbaB8UeGt2YWKHW7Lx1nm6Q"
    chart_url = "https://api.chart-img.com/v2/tradingview/advanced-chart"
    headers = {"x-api-key": chart_api_key, "content-type": "application/json"}
    chart_payload = {
        "theme": "dark",
        "interval": "1h",
        "symbol": symbol,
        "override": {"showStudyLastValue": True},
        "studies": [
            {"name": "Volume", "forceOverlay": False},
            {
                "name": "Ichimoku Cloud",
                "input": {"in_0": 9, "in_1": 26, "in_2": 52, "in_3": 26},
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
                    "Plots Background.transparency": 90,
                },
            },
            {
                "name": "Relative Strength Index",
                "forceOverlay": False,
                "input": {"length": 14, "smoothingLine": "SMA", "smoothingLength": 14},
                "override": {
                    "Plot.visible": True,
                    "Plot.linewidth": 1,
                    "Plot.plottype": "line",
                    "Plot.color": "rgb(126,87,194)",
                    "Smoothed MA.visible": True,
                    "Smoothed MA.linewidth": 1,
                    "Smoothed MA.plottype": "line",
                    "Smoothed MA.color": "rgb(33,150,243)",
                    "UpperLimit.visible": True,
                    "UpperLimit.linestyle": 2,
                    "UpperLimit.linewidth": 1,
                    "UpperLimit.value": 75,
                    "UpperLimit.color": "rgb(120,123,134)",
                    "LowerLimit.visible": True,
                    "LowerLimit.linestyle": 2,
                    "LowerLimit.linewidth": 1,
                    "LowerLimit.value": 25,
                    "LowerLimit.color": "rgb(120,123,134)",
                },
            },
        ],
    }
    try:
        chart_response = requests.post(chart_url, headers=headers, json=chart_payload)
        image_buffer = io.BytesIO(chart_response.content)
        await update.effective_message.reply_photo(
            photo=image_buffer, caption=query.data
        )
    except Exception as e:
        print(e)
        await update.effective_message.reply_text(
            text="Sorry, meet limit request today. Please try again tomorrow."
        )


# Check trading conditions and send message to Telegram
tokens_to_check = [
    "BTCUSDT",
    "UNIUSDT",
    "MAVUSDT",
    "OPUSDT",
    "UNFIUSDT",
    "DOGEUSDT",
    "SUIUSDT",
    "BAKEUSDT",
    "AUDIOUSDT",
    "GRTUSDT",
    "LITUSDT",
    "BELUSDT",
    "RENUSDT",
    "LINKUSDT",
    "RUNEUSDT",
]

# Funtion in JobQueue


def time_to_next_hour(target_minute, current_time=None):
    current_time = datetime.datetime.now()
    next_hour = current_time.replace(
        minute=0, second=0, microsecond=0
    ) + datetime.timedelta(minutes=target_minute)
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
        if job_removed:
            text = "Previous checking is stopped!"
            await update.effective_message.reply_text(text)
        target_minute = 50
        current_time = datetime.datetime.now()
        time_to_wait = time_to_next_hour(target_minute, current_time)
        if time_to_wait < 0:
            time_to_wait += 3600
        context.job_queue.run_repeating(
            check_conditions_and_send_message,
            interval=3600,
            first=time_to_wait,
            chat_id=chat_id,
            name=str(chat_id),
        )

        text = "Checking conditions every hour..."
        await update.effective_message.reply_text(
            f"{text} Time to wait: {time_to_wait} seconds"
        )
    except (IndexError, ValueError):
        await update.effective_message.reply_text("Usage: /start_checking")


async def check_conditions_and_send_message(context: ContextTypes.DEFAULT_TYPE):
    print("Checking conditions...")
    job = context.job
    for symbol in tokens_to_check:
        symbol_data = get_symbol_data(symbol)
        current_price = float(symbol_data.iloc[-1]["Close price"])
        open_price = float(symbol_data.iloc[-1]["Open price"])
        current_volume = float(symbol_data.iloc[-1]["Volume"])
        list_volume, list_close_price = get_symbol_history(symbol)
        ma20_volume = calculate_last_ma(list_volume, 20)
        volume_threshold = 1.3
        rsi = calculate_rsi(list_close_price)
        rsi = calculate_rsi(list_close_price)
        conditions = {
            "cross_ma": current_price > open_price
            and ma_crossover_signal(list_close_price),
            "macd": macd_crossover_signal(list_close_price),
            "break_volume": current_volume > ma20_volume * volume_threshold,
            "under_cloud": is_price_upper_cloud(list_close_price),
        }
        signal_strength = sum(conditions.values())
        true_conditions = [
            condition for condition, is_true in conditions.items() if is_true
        ]

        signal_texts = {4: "Strong buy", 3: "Buy", 2: "Low signal"}

        signal_text = signal_texts.get(signal_strength, "Sell")
        reasons = {
            "cross_ma": "Crossed Moving Averages",
            "macd": "MACD Crossover",
            "break_volume": "Break Volume",
            "under_cloud": "Price Under Cloud",
        }

        reason = reasons.get(true_conditions[0], "")

        #! Send message to telegram
        message = (
            f"🚀{signal_text.upper()} {symbol}\n"
            f"💸Price: {current_price}\n"
            f"💸Open Price: {open_price}\n"
            f"⬆️Volume: {current_volume}\n"
            f"MA20 Volume: {ma20_volume}\n"
            f"Reason: {reason}"
        )

        #
        if (
            current_price > open_price
            and current_volume > ma20_volume * volume_threshold
        ):
            keyboard = [
                [
                    InlineKeyboardButton(
                        text=f"View Chart {symbol}", callback_data=symbol
                    )
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            # message = f"🚀{signal_text.upper()} {symbol}\n💸Price: {current_price}\n💸Open Price: {open_price}\n⬆️Volume: {current_volume}\nMA20 Volume: {ma20_volume}\nReason: Break Volume"
            await context.bot.send_message(
                job.chat_id, text=message, reply_markup=reply_markup
            )
        elif (
            current_price < open_price
            and current_volume > ma20_volume * volume_threshold
        ):
            keyboard = [
                [
                    InlineKeyboardButton(
                        text=f"View Chart {symbol}", callback_data=symbol
                    )
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            # message = f"🚀{signal_text.upper()} {symbol}\n💸Price: {current_price}\n💸Open Price: {open_price}\n⬆️Volume: {current_volume}\nMA20 Volume: {ma20_volume}\nReason: Break Volume"
            await context.bot.send_message(
                job.chat_id, text=message, reply_markup=reply_markup
            )
        elif rsi < 20:
            keyboard = [
                [
                    InlineKeyboardButton(
                        text=f"View Chart {symbol}", callback_data=symbol
                    )
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            message = f"🚀BUY SIGNAL {symbol}\n💸Price: {current_price}\n💸Open Price: {open_price}\n⬆️Volume: {current_volume}\nMA20 Volume: {ma20_volume}\nRSI: {rsi}\nReason: RSI oversold"
            await context.bot.send_message(
                job.chat_id, text=message, reply_markup=reply_markup
            )
        elif rsi > 75:
            keyboard = [
                [
                    InlineKeyboardButton(
                        text=f"View Chart {symbol}", callback_data=symbol
                    )
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            message = f"📉SELL SIGNAL {symbol}\n💸Price: {current_price}\n💸Open Price: {open_price}\n⬆️Volume: {current_volume}\nMA20 Volume: {ma20_volume}\nRSI: {rsi}\nReason: RSI overbought"
            await context.bot.send_message(
                job.chat_id, text=message, reply_markup=reply_markup
            )
        else:
            print(f"No buy signal for {symbol}")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends explanation on how to use the bot."""
    await update.message.reply_text(
        "Bào sàn binance nè\n /start_checking để bắt đầu theo dõi \n /stop_checking để dừng \n /listtoken để xem danh sách token \n /addtoken để thêm token \n /removetoken để xóa token"
    )


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
        await update.message.reply_text(text=f"Removed {new_token} from the list.")
    except (IndexError, ValueError):
        await update.message.reply_text("Usage: /remove_token <token>")


def main() -> None:
    """Run bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(TOKEN).build()

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler(["start", "help"], start))
    application.add_handler(CommandHandler("start_checking", start_checking))
    application.add_handler(CommandHandler("list_token", return_list_token))
    application.add_handler(CommandHandler("add_token", add_token))
    application.add_handler(CommandHandler("remove_token", remove_token))
    application.add_handler(CommandHandler("stop_checking", stop_checking))
    application.add_handler(CallbackQueryHandler(send_chart))

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
