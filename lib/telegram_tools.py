from diary.models import User
import telegram
from telegram import Update
from telegram.ext import (
    ContextTypes,
)
from lib.utils import parse_multiple_choice


async def send_telegram_message(
    user: User, context: ContextTypes.DEFAULT_TYPE, message: str
):

    matches = parse_multiple_choice(message)
    if matches:
        keyboard = [[telegram.KeyboardButton(match)] for match in matches]
        keyboard_markup = telegram.ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    else:
        keyboard_markup = {"remove_keyboard": True}

    # Send to telegram
    telegram_message = await context.bot.send_message(
        chat_id=user.chat_id, text=message, reply_markup=keyboard_markup
    )
    return telegram_message


async def send_typing_animation(context, user):
    await context.bot.send_chat_action(
        chat_id=user.chat_id,
        action=telegram.constants.ChatAction.TYPING,
    )
