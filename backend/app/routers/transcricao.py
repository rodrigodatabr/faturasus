"""Router de transcrição de áudio via OpenAI Whisper."""

from io import BytesIO

from fastapi import APIRouter, File, HTTPException, UploadFile
from openai import AsyncOpenAI

from app.config import settings

router = APIRouter()
_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)


@router.post("/transcricao")
async def transcrever(audio: UploadFile = File(...)):
    """Recebe áudio (multipart), transcreve via Whisper e retorna o texto."""
    conteudo = await audio.read()
    buffer = BytesIO(conteudo)
    content_type = audio.content_type or "audio/webm"
    filename = audio.filename or "audio.webm"

    try:
        resultado = await _client.audio.transcriptions.create(
            model="whisper-1",
            file=(filename, buffer, content_type),
            language="pt",
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return {"texto": resultado.text}
