import os
import django
from asgiref.sync import sync_to_async

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "DiaryDjangoOrm.settings")
django.setup()


async def persist_message(user, message):
    await sync_to_async(user.messages.create)(
        user=user,
        text=message,
        author="User",
        source="TelegramText",
    )
