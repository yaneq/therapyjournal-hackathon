import os
import time
from openai import OpenAI
from dotenv import load_dotenv
from asgiref.sync import sync_to_async
from diary.models import User

from .open_ai_tools import get_open_ai_client
from lib.dates import get_date_prefix
from lib.env import env

# load_dotenv()


async def create_thread(user, open_ai_client):
    """
    Creates a thread for the given user on the current OpenAI Assistant
    Used when a user does not have an active thread with an Assistant
    """

    thread = open_ai_client.beta.threads.create()
    return thread


async def get_thread(thread_id):
    open_ai_client = get_open_ai_client()
    return open_ai_client.beta.threads.retrieve(thread_id)


async def get_or_create_thread(user):
    """
    Takes a user id parameter and finds the thread on this program's OpenAI Assistant for that user
    If the user does not have a thread it calls the create thread function
    """

    open_ai_client = get_open_ai_client()
    if user.thread_id:
        thread_id = user.thread_id
        thread = get_thread(thread_id)
    else:
        print("Creating new thread", user, open_ai_client)
        thread = create_thread(user, open_ai_client)
        user.thread_id = thread.id
        await sync_to_async(user.save)()

    return thread


async def retrieve_thread_status(thread_id: str):
    open_ai_client = get_open_ai_client()
    thread = open_ai_client.beta.threads.retrieve(thread_id)
    return thread.status


async def send_message_to_assistant(user: User, message: str):
    open_ai_client = get_open_ai_client()

    message_with_date = get_date_prefix() + message

    # Send message to OpenAI Assistant
    open_ai_client.beta.threads.messages.create(
        thread_id=user.thread_id,
        role="user",
        content=message_with_date,
    )

    # run therapy assistant with new message
    run = open_ai_client.beta.threads.runs.create(
        thread_id=user.thread_id, assistant_id=env("ASSISTANT_ID")
    )

    while run.status not in ["completed", "failed"]:
        run = open_ai_client.beta.threads.runs.retrieve(
            thread_id=user.thread_id, run_id=run.id
        )
        time.sleep(1)

    if run.status == "failed":
        # Log error details if available
        error_message = run.last_error.code if run.last_error else "Unknown error"
        print(f"Run failed with error: {error_message}")
        # Handle the error appropriately - you might raise an exception or return an error message
        raise Exception(f"Failed to complete run: {error_message}")

    if run.status == "completed":
        messages = open_ai_client.beta.threads.messages.list(thread_id=user.thread_id)
        assistant_prompt_text = messages.data[0].content[0].text.value
        return assistant_prompt_text
