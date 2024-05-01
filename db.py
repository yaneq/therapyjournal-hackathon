import os
import django
from asgiref.sync import sync_to_async

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "DiaryDjangoOrm.settings")
django.setup()


async def persist_message(
    user,
    message: str,
    telegram_message_id: int,
    author: str = "User",
    source: str = "TelegramText",
):
    await sync_to_async(user.messages.create)(
        user=user,
        text=message,
        author=author,
        source=source,
        telegram_message_id=telegram_message_id,
    )
