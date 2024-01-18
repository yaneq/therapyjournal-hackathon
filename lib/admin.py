from lib.config import Config


config = Config.load()


async def user_log(user, context, message):
    await context.bot.send_message(
        chat_id=config.admin_chat_id,
        text=f"User Log ({user.first_name}): {message}",
    )
