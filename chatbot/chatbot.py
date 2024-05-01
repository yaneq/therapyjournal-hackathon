from asgiref.sync import sync_to_async
import logging
from os import getenv
from telegram import Update
import telegram
import datetime

from lib.dates import get_date_prefix
import db
from db import persist_message
from telegram.ext import (
    filters,
    MessageHandler,
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)
from chatbot.week_in_review import send_week_in_review
import re


from diary.models import User
from lib.admin import user_log
from lib.assistant import suggest_improvements
from lib.threads import create_thread, send_message_to_assistant

# from lib.therapist import analyze_journal
from lib.open_ai_tools import get_open_ai_client
from lib.utils import remove_command_string
from lib.env import env
from lib.telegram_tools import send_telegram_message, send_typing_animation
from lib.whisper_tools import audio_to_text

from django.core.exceptions import ObjectDoesNotExist
import sentry_sdk


sentry_sdk.init(
    dsn=env("SENTRY_DSN"),
    enable_tracing=True,
)

from lib.config import Config

config = Config.load()

# MIN_MESSAGE_LENGTH_FOR_REFLECTION = 200

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.DEBUG
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    open_ai_client = get_open_ai_client()
    user = await get_user(update)
    thread = await create_thread(user, open_ai_client)
    user.thread_id = thread.id
    await sync_to_async(user.save)()

    reply = await send_message_to_assistant(user, "Hello")

    # Send to telegram
    telegram_message = await send_telegram_message(user, context, reply)

    # Archive therapist message
    db_message = await sync_to_async(user.messages.create)(
        user=user,
        text=reply,
        author="TherapistBot",
        telegram_message_id=telegram_message.message_id,
    )

    await user_log(user, context, "New user")


async def get_user(update):
    chat_id = update.effective_chat.id
    try:
        user = await sync_to_async(User.objects.get)(chat_id=chat_id)
    except ObjectDoesNotExist:
        user = await sync_to_async(User.objects.create)(
            chat_id=chat_id,
            first_name=update.effective_user.first_name,
            last_name=update.effective_user.last_name,
        )
    return user


async def new_entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = await get_user(update)
    text = update.message.text
    await persist_message(user, text, update.message.id)

    send_typing_animation(context, user)

    try:
        reply = await send_message_to_assistant(user, text)
    except Exception as e:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=str(e))
        return

    telegram_message = await send_telegram_message(user, context, reply)

    await persist_message(
        user, reply, telegram_message.message_id, author="TherapistBot"
    )


# async def reflect(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     user = await get_user(update)
#     combined = ""
#     async for message in user.messages.filter(author="User", processed=False):
#         combined += message.text + "\n\n"

#     if len(combined) < MIN_MESSAGE_LENGTH_FOR_REFLECTION:
#         await context.bot.send_message(
#             chat_id=update.effective_chat.id,
#             text=f"Analysis will be more helpful if you write at last {MIN_MESSAGE_LENGTH_FOR_REFLECTION - len(combined)} more characters before reflecting.",
#         )
#     else:
#         await context.bot.send_chat_action(
#             chat_id=update.effective_chat.id,
#             action=telegram.constants.ChatAction.TYPING,
#         )

#         # Obtain analysis
#         analysis = analyze_journal(user, combined)

#         # Send to telegram
#         telegram_message = await context.bot.send_message(
#             chat_id=update.effective_chat.id, text=analysis
#         )
#         # Archive therapist message
#         message = await sync_to_async(user.messages.create)(
#             user=user,
#             text=analysis,
#             author="TherapistBot",
#             telegram_message_id=telegram_message.message_id,
#         )
#         # Mark existing messages as processed
#         await sync_to_async(user.messages.filter(author="User").update)(processed=True)


async def get_goal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = await get_user(update)
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"Your current goal is: {user.goal}",
    )


async def get_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = await get_user(update)
    # collect journal statistics
    message_count = await sync_to_async(user.messages.filter(author="User").count)()
    unprocessed_count = await sync_to_async(
        user.messages.filter(processed=False, author="User").count
    )()

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"You have {unprocessed_count} / {message_count} unprocessed journal entries.",
    )


async def transcribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = await get_user(update)
    transcript = await audio_to_text(context, update.message.voice.file_id)
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"Transcription: {transcript}"[:4000],
    )
    await persist_message(user, transcript, update.message.id, source="TelegramVoice")

    send_typing_animation(context, user)

    try:
        reply = await send_message_to_assistant(user, transcript)
    except Exception as e:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=str(e))
        return

    send_typing_animation(context, user)
    telegram_message = await send_telegram_message(user, context, reply)

    await persist_message(
        user, reply, telegram_message.message_id, author="TherapistBot"
    )


async def set_challenges(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = await get_user(update)

    challenges = remove_command_string(update.message.text)

    messages_last_week = user.messages.filter(
        created_date__gte=datetime.datetime.now() - datetime.timedelta(weeks=1),
        author="User",
    )

    combined = ""
    async for message in messages_last_week:
        combined += message.text + "\n\n"

    improvements = await suggest_improvements(user, challenges, combined)

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=improvements,
    )

    message = await sync_to_async(user.messages.create)(
        text=improvements,
        author="RetroBot",
    )


async def send_week_in_review_wrapper(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    user = await get_user(update)
    await send_week_in_review(user, context.bot)


async def reminders_switch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = await get_user(update)
    command = remove_command_string(update.message.text)
    reminders_on = command == "/reminders_on"
    user.enable_reminders = reminders_on
    await sync_to_async(user.save)()
    user_message = f"Reminders switched {'on' if reminders_on else 'off'}"
    await send_telegram_message(user, context, user_message)
    await user_log(user, context, user_message)


async def weekly_review_switch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = await get_user(update)
    command = remove_command_string(update.message.text)
    weekly_review_on = command == "on"
    user.enable_week_in_review = weekly_review_on
    await sync_to_async(user.save)()
    await send_telegram_message(
        user, context, f"Weekly review switched {'on' if weekly_review_on else 'off'}"
    )


def serve_bot():
    application = ApplicationBuilder().token(env("TELEGRAM_BOT_TOKEN")).build()

    # Command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("goal", get_goal))
    application.add_handler(CommandHandler("info", get_info))
    # application.add_handler(CommandHandler("reflect", reflect))
    application.add_handler(
        CommandHandler("week_in_review", send_week_in_review_wrapper)
    )
    application.add_handler(CommandHandler("weekly_review", weekly_review_switch))
    application.add_handler(CommandHandler("reminders_on", reminders_switch))
    application.add_handler(CommandHandler("reminders_off", reminders_switch))

    # Regular message handler
    application.add_handler(
        MessageHandler(filters.TEXT & (~filters.COMMAND), new_entry)
    )

    # Non-text handlers
    application.add_handler(
        MessageHandler(filters.VOICE & (~filters.COMMAND), transcribe)
    )

    application.run_polling()
