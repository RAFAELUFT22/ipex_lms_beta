import requests
import json
import os

# --- CONFIGURAÇÃO OPENROUTER (LMS LITE) ---
OPENROUTER_API_KEY = "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"
MODEL = "google/gemini-2.0-flash-lite-001" # Modelo Econômico e Multimodal (Audio-Ready)

def ask_tutor_lite(student_whatsapp, student_message, course_context="Audiovisual"):
    # 1. Busca dados do aluno no nosso novo DB Lite
    try:
        student_res = requests.get(f"http://localhost:8081/student/{student_whatsapp}")
        student_data = student_res.json()
    except Exception as e:
        print(f"Erro ao buscar aluno: {e}")
        student_data = {"name": "Estudante", "sisec_data": {}}

    # 2. Constrói o Prompt com Identidade TDS e Otimização de Voz
    system_prompt = f"""
    VOCÊ É O TUTOR IA DO PROJETO TDS (TERRITÓRIO DE DESENVOLVIMENTO SOCIAL).
    Sua missão é ajudar o aluno: {student_data.get('name', 'Estudante')}.
    Contexto do Aluno (SISEC): {json.dumps(student_data.get('sisec_data', {}))}
    Curso Atual: {course_context}

    DIRETRIZES DE RESPOSTA (OTIMIZADAS PARA VOZ):
    - Seja extremamente direto e acolhedor.
    - REGRAS DE ÁUDIO: Evite listas numeradas extensas, tabelas ou negritos em excesso.
    - Use frases curtas. Sua resposta será lida por um motor de voz.
    - Se o aluno for rural, use analogias simples (como o ciclo da colheita).
    - LIMITE: Tente responder em no máximo 300 caracteres para manter a fluidez do áudio.
    """

    # 3. Chamada OpenRouter
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "HTTP-Referer": "https://ipexdesenvolvimento.cloud",
        "X-Title": "TDS LMS Lite (Voz)"
    }

    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": student_message}
        ]
    }

    try:
        response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload)
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
        else:
            return f"Desculpe, tive um probleminha técnico. Erro {response.status_code}."
    except Exception as e:
        return f"Ops! Houve uma falha na conexão. Tente novamente mais tarde."

if __name__ == "__main__":
    # Teste rápido
    print("--- TESTE DE VOZ ---")
    print(ask_tutor_lite("5563999374165", "Como eu faço para editar um vídeo no celular?"))
