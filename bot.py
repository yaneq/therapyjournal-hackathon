import asyncio
import sys
from chatbot.chatbot import serve_bot
from chatbot.trigger_interaction import trigger_interaction_for_all

HELP_MESSAGE = "Runs the bot commands\n\
\n\
Syntax:\n\
bot.py [command]:\n\
\n\
 command:\n\
\n\
 - serve:               Starts the bot and polls new messages\n\
- good_morning:         Pings the bot to initiate a conversation\n\
- good_evening:         Pings the bot to initiate a conversation\n\
"

if __name__ == "__main__":
    if len(sys.argv) > 1:
        command = sys.argv[1]
        match command:
            case "serve":
                serve_bot()
            case "good_morning":
                asyncio.run(trigger_interaction_for_all("start-morning-check-in"))
            case "good_evening":
                asyncio.run(trigger_interaction_for_all("start-evening-check-in"))

            case _:
                print(HELP_MESSAGE)
    else:
        print(HELP_MESSAGE)
