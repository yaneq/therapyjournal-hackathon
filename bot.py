import asyncio
import sys
from chatbot.chatbot import serve_bot
from chatbot.trigger_interaction import trigger_interaction_for_all
from chatbot.week_in_review import send_week_in_review_to_all

HELP_MESSAGE = "Runs the bot commands\n\
\n\
Syntax:\n\
bot.py [command]:\n\
\n\
 command:\n\
\n\
 - serve:               Starts the bot and polls new messages\n\
- send_week_in_review:      Sends a summary of the week to all user that have\n\
                            enable_week_in_review flag turned on.\n\
                            This should be executed by a cron-job.\n\
- good_morning:         Pings the bot to initiate a conversation\n\
- good_evening:         Pings the bot to initiate a conversation\n\
"

if __name__ == "__main__":
    if len(sys.argv) > 1:
        command = sys.argv[1]
        match command:
            case "serve":
                serve_bot()
            case "send_week_in_review":
                asyncio.run(send_week_in_review_to_all())
            case "good_morning":
                asyncio.run(trigger_interaction_for_all("start-morning-check-in"))
            case "good_evening":
                asyncio.run(trigger_interaction_for_all("start-evening-check-in"))

            case _:
                print(HELP_MESSAGE)
    else:
        print(HELP_MESSAGE)
