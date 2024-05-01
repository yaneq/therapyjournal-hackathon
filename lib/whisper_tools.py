import io

from lib.open_ai_tools import get_open_ai_client


async def audio_to_text(context, file_id):
    audio_file = await context.bot.get_file(file_id)
    buffer = io.BytesIO()
    buffer.name = "InMemory.ogg"
    await audio_file.download_to_memory(buffer)
    open_ai_client = get_open_ai_client()
    transcript = open_ai_client.audio.transcriptions.create(
        model="whisper-1", file=buffer, response_format="verbose_json"
    )
    return transcript.text
