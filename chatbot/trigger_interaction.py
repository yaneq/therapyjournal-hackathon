from lib.config import Config
from lib.env import env
from telegram.ext import ApplicationBuilder
import db
from diary.models import User
from lib.threads import send_message_to_assistant

config = Config.load()


async def trigger_interaction(user, bot, prompt):
    reply = await send_message_to_assistant(user, prompt)
    telegram_message = await bot.send_message(
        chat_id=user.chat_id,
        text=reply,
    )

    await db.persist_message(
        user, reply, telegram_message.message_id, author="TherapistBot"
    )


async def trigger_interaction_for_all(prompt):
    application = ApplicationBuilder().token(env("TELEGRAM_BOT_TOKEN")).build()
    async for user in User.objects.filter(enable_reminders=True).all():
        await trigger_interaction(user, application.bot, prompt)
