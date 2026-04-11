import os
import json
import subprocess
import sys
import re

# Configurações
SYSTEM_PROMPT_PATH = "/root/.gemini/antigravity/brain/f26a7d09-35ca-4a3b-bd50-acd4e574031b/tutor_ia_system_prompt.md"

def get_system_instruction():
    with open(SYSTEM_PROMPT_PATH, 'r') as f:
        content = f.read()
        # Extrai apenas a parte da instrução do markdown
        start_marker = "## System Instruction / System Prompt"
        end_marker = "## Como configurar"
        try:
            prompt = content.split(start_marker)[1].split(end_marker)[0].strip()
            return prompt
        except:
            return content

def run_tutor(message, student_context_json=None):
    system_instruction = get_system_instruction()
    
    # Adiciona o contexto do aluno se fornecido
    if student_context_json:
        context_str = f"\n\n[PERFIL SISEC DO ALUNO]\n{json.dumps(student_context_json, ensure_ascii=False)}"
        system_instruction += context_str

    # Comando para o Gemini CLI (assumindo que o gemini aceita --system-instruction)
    # Ajuste o comando conforme a sintaxe real do seu CLI
    try:
        # Usando subprocess para chamar o binário 'gemini'
        # Nota: Se o seu gemini-cli usar outros flags, ajuste aqui.
        cmd = ["gemini", "chat", "--system-instruction", system_instruction, message]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        response = result.stdout
        
        # Extração de Métricas (Tags)
        metrics = re.findall(r"\[TRACK: (.*?)\]", response)
        
        # Limpa a resposta para o usuário final
        clean_response = re.sub(r"\[TRACK: (.*?)\]", "", response).strip()
        
        return {
            "response": clean_response,
            "metrics": metrics
        }
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python3 tutor_cli.py 'mensagem do aluno' [json_aluno]")
        sys.exit(1)

    msg = sys.argv[1]
    context = None
    if len(sys.argv) > 2:
        try:
            # Tenta ler o JSON do argumento ou do arquivo
            raw_context = sys.argv[2]
            if os.path.exists(raw_context):
                with open(raw_context, 'r') as f:
                    context = json.load(f)
            else:
                context = json.loads(raw_context)
            
            # Anonimiza antes de enviar
            from sisec_anonymizer import anonymize_sisec
            context = anonymize_sisec(context)
        except:
            pass

    res = run_tutor(msg, context)
    print(json.dumps(res, indent=2, ensure_ascii=False))
