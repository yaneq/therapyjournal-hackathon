from telegram import Update
from telegram.ext import ContextTypes
from asgiref.sync import sync_to_async
import datetime
from admin import user_log
import db
from db import persist_message
from lib.assistant import suggest_improvements
from lib.threads import create_thread, send_message_to_assistant
from lib.utils import remove_command_string
from lib.whisper_tools import audio_to_text
from lib.telegram_tools import send_telegram_message, send_typing_animation
from diary.models import User
from django.core.exceptions import ObjectDoesNotExist


async def get_user(update: Update):
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


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    open_ai_client = get_open_ai_client()
    user = await get_user(update)
    thread = await create_thread(user, open_ai_client)
    user.thread_id = thread.id
    await sync_to_async(user.save)()

    reply = await send_message_to_assistant(user, "Hello")
    telegram_message = await send_telegram_message(user, context, reply)
    await sync_to_async(user.messages.create)(
        user=user,
        text=reply,
        author="TherapistBot",
        telegram_message_id=telegram_message.message_id,
    )
    await user_log(user, context, "New user")


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


async def get_goal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = await get_user(update)
    await context.bot.send_message(
        chat_id=update.effective_chat.id, text=f"Your current goal is: {user.goal}"
    )


async def get_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = await get_user(update)
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
        chat_id=update.effective_chat.id, text=f"Transcription: {transcript}"[:4000]
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
        created_date__gte=datetime.datetime.now() - datetime.timedelta(weeks=1)
    )
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"You have {messages_last_week.count()} messages in the last week.",
    )
    user.challenges = challenges
    await sync_to_async(user.save)()
    await context.bot.send_message(
        chat_id=update.effective_chat.id, text=f"Challenges set to: {challenges}"
    )


async def suggest_improvements(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = await get_user(update)
    suggestions = await suggest_improvements(user)
    await context.bot.send_message(chat_id=update.effective_chat.id, text=suggestions)


async def reminders_switch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = await get_user(update)
    command = remove_command_string(update.message.text)
    reminders_on = command == "/reminders_on"
    user.enable_reminders = reminders_on
    await sync_to_async(user.save)()
    user_message = f"Reminders switched {'on' if reminders_on else 'off'}"
    await send_telegram_message(user, context, user_message)
    await user_log(user, context, user_message)
