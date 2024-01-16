from lib.config import Config
from lib.env import env
from lib.assistant import summarize_week
from asgiref.sync import sync_to_async
from telegram.ext import ApplicationBuilder
from datetime import datetime, timedelta
import db
from diary.models import User
from lib.threads import send_message_to_assistant

config = Config.load()


async def trigger_interaction(user, bot, prompt):
    reply = await send_message_to_assistant(
        user, prompt, config.assistant_id_life_coach
    )
    await bot.send_message(
        chat_id=user.chat_id,
        text=reply,
    )

    message = await sync_to_async(user.messages.create)(
        text=reply,
        author="TherapistBot",
    )


async def trigger_interaction_for_all(prompt):
    application = ApplicationBuilder().token(env("TELEGRAM_BOT_TOKEN")).build()
    async for user in User.objects.filter(enable_reminders=True).all():
        await trigger_interaction(user, application.bot, prompt)
