from fastapi import FastAPI, Request
import requests

# ===== CHAVES DO JSON ORIGINAL =====

GROQ_API_KEY = "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"

EVOLUTION_URL = "https://evolution-api-production-ff207.up.railway.app"
EVOLUTION_API_KEY = "minhachave123"
EVOLUTION_INSTANCE = "apice2027"

# ==================================

app = FastAPI(title="Backend WhatsApp IA - Clinica Saude Total")


def gerar_resposta(mensagem: str) -> str:
    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "Voce e assistente da Clinica Saude Total. "
                        "Responda em portugues de forma cordial e profissional. "
                        "Seja breve e objetiva."
                    )
                },
                {
                    "role": "user",
                    "content": mensagem
                }
            ]
        },
        timeout=60
    )

    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]


def enviar_whatsapp(numero: str, texto: str):
    response = requests.post(
        f"{EVOLUTION_URL}/message/sendText/{EVOLUTION_INSTANCE}",
        headers={
            "apikey": EVOLUTION_API_KEY,
            "Content-Type": "application/json"
        },
        json={
            "number": numero,
            "text": texto
        },
        timeout=60
    )

    response.raise_for_status()

    try:
        return response.json()
    except Exception:
        return {"raw": response.text}


@app.get("/")
def home():
    return {
        "status": "online",
        "mensagem": "Backend WhatsApp IA funcionando"
    }


@app.post("/webhook")
async def webhook(request: Request):
    body = await request.json()

    try:
        data = body.get("data", {})
        key = data.get("key", {})
        message = data.get("message", {})

        if not message:
            return {"status": "ignorado", "motivo": "sem mensagem"}

        if key.get("fromMe") is True:
            return {"status": "ignorado", "motivo": "mensagem enviada por mim"}

        texto = (
            message.get("conversation")
            or message.get("extendedTextMessage", {}).get("text")
            or message.get("imageMessage", {}).get("caption")
            or ""
        )

        texto = (
            texto
            .replace("\r", " ")
            .replace("\n", " ")
            .replace("\t", " ")
            .replace('"', " ")
            .replace("\\", " ")
            .strip()
        )

        if not texto:
            return {"status": "ignorado", "motivo": "sem texto"}

        telefone = (
            key.get("remoteJid", "")
            .replace("@s.whatsapp.net", "")
            .replace("@g.us", "")
        )

        if not telefone:
            return {"status": "erro", "motivo": "telefone nao encontrado"}

        resposta = gerar_resposta(texto)
        resposta_limpa = resposta.replace("\r", " ").replace("\n", " ").strip()

        envio = enviar_whatsapp(telefone, resposta_limpa)

        return {
            "status": "ok",
            "telefone": telefone,
            "mensagem_recebida": texto,
            "resposta_enviada": resposta_limpa,
            "evolution": envio
        }

    except Exception as e:
        return {
            "status": "erro",
            "mensagem": str(e)
        }
