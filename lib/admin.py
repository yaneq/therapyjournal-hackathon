from lib.env import env


async def user_log(user, context, message):
    await context.bot.send_message(
        chat_id=env("ADMIN_CHAT_ID"),
        text=f"User Log ({user.first_name}): {message}",
    )
