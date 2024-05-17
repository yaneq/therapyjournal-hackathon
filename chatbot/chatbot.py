import logging
from chatbot.handlers import (
    get_goal,
    get_info,
    new_entry,
    reminders_switch,
    start,
    transcribe,
)

from telegram.ext import (
    filters,
    MessageHandler,
    ApplicationBuilder,
    CommandHandler,
)
from lib.env import env
import sentry_sdk


sentry_sdk.init(
    dsn=env("SENTRY_DSN"),
    enable_tracing=True,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.DEBUG
)


def serve_bot():
    application = ApplicationBuilder().token(env("TELEGRAM_BOT_TOKEN")).build()

    # Command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("goal", get_goal))
    application.add_handler(CommandHandler("info", get_info))

    application.add_handler(CommandHandler("reminders_on", reminders_switch))
    application.add_handler(CommandHandler("reminders_off", reminders_switch))

    application.add_handler(
        MessageHandler(filters.TEXT & (~filters.COMMAND), new_entry)
    )

    # Non-text handlers
    application.add_handler(
        MessageHandler(filters.VOICE & (~filters.COMMAND), transcribe)
    )

    application.run_polling()
