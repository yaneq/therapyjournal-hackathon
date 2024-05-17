from dotenv import load_dotenv
from os import getenv
import time

from lib.threads import create_thread

from .open_ai_tools import get_open_ai_client

load_dotenv()

RETRO_ASSISTANT_ID = "asst_5VFsiTgOoMpVf4oUIMuDHiiH"


def suggest_improvements(user, challenge, diary_entries):
    open_ai_client = get_open_ai_client()
    thread = create_thread(user, open_ai_client)

    message = open_ai_client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=f"These are the journal entries for this user for the past week: \n\
<START OF JOURNEY ENTRIES>\n\
{diary_entries}\n\
<END OF JOURNEY ENTRIES>\n\
\n\
The user states that this is is current main challenge: {challenge}",
    )

    # run therapy assistant with new message
    run = open_ai_client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=RETRO_ASSISTANT_ID,
        instructions="Please return the answer in the format of bullet points.",
    )

    # wait for run to complete
    while run.status != "completed":
        # print(run)
        run = open_ai_client.beta.threads.runs.retrieve(
            thread_id=thread.id, run_id=run.id
        )
        time.sleep(2)

    # get messages to print out response for therapist
    messages = open_ai_client.beta.threads.messages.list(thread_id=thread.id)
    assistant_prompt_text = messages.data[0].content[0].text.value
    return assistant_prompt_text
