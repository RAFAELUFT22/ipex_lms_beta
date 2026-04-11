import json
import os

file_path = "/root/projeto-tds/n8n-workflows/tds-auth-rag-flow.json"

with open(file_path, "r") as f:
    flow = json.load(f)

# 1. Atualiza a URL do AnythingLLM para o workspace correto
for node in flow["nodes"]:
    if node["name"] == "AnythingLLM (RAG)":
        node["parameters"]["url"] = "http://anythingllm:3001/api/v1/workspace/tds-audiovisual-e-conteudo/chat"

# 2. Adiciona IF de Comandos antes do AnythingLLM
# Em "Aluno Cadastrado?", a saída True (index 0) ia para AnythingLLM (RAG).
# Agora, "Aluno Cadastrado?" vai para "If Comandos"
# "If Comandos" true -> "AnythingLLM (RAG)" ou "Responder Ajuda"

if_comandos_node = {
    "parameters": {
        "conditions": {
            "options": {
                "caseSensitive": False,
                "leftValue": "",
                "typeValidation": "strict"
            },
            "conditions": [
                {
                    "id": "comando-tds",
                    "leftValue": "={{ $('Configurador de Dados').item.json.messageText }}",
                    "rightValue": "/tds",
                    "operator": {
                        "type": "string",
                        "operation": "startsWith"
                    }
                }
            ],
            "combinator": "and"
        }
    },
    "id": "node-if-comandos",
    "name": "Se Comando RAG",
    "type": "n8n-nodes-base.if",
    "typeVersion": 2,
    "position": [700, 250]
}

ajuda_node = {
    "parameters": {
        "conditions": {
            "options": {
                "caseSensitive": False,
                "leftValue": "",
                "typeValidation": "strict"
            },
            "conditions": [
                {
                    "id": "comando-ajuda",
                    "leftValue": "={{ $('Configurador de Dados').item.json.messageText }}",
                    "rightValue": "/ajuda",
                    "operator": {
                        "type": "string",
                        "operation": "startsWith"
                    }
                }
            ],
            "combinator": "and"
        }
    },
    "id": "node-if-ajuda",
    "name": "Se Comando Ajuda",
    "type": "n8n-nodes-base.if",
    "typeVersion": 2,
    "position": [700, 100]
}

send_ajuda_node = {
    "parameters": {
        "method": "POST",
        "url": "=https://evolution.ipexdesenvolvimento.cloud/message/sendText/kreativ",
        "sendHeaders": True,
        "headerParameters": {
            "parameters": [
                { "name": "apikey", "value": "{{ $env.EVOLUTION_API_KEY }}" }
            ]
        },
        "sendBody": True,
        "bodyParameters": {
            "parameters": [
                { "name": "number", "value": "={{ $('Configurador de Dados').item.json.phoneNumber }}" },
                { "name": "text", "value": "🤖 *Olá! Eu sou o assistente do Projeto TDS.*\n\nComo estamos num ambiente de grupo, eu só respondo quando você usar comandos! Isso evita que eu interrompa a conversa de vocês.\n\nUse:\n👉 `/tds [sua pergunta]` para tirar dúvidas sobre vídeo, roteiro e tudo do curso!\n\nExemplo: `/tds Como começar a gravar num celular básico?`" }
            ]
        },
        "options": {}
    },
    "id": "node-send-ajuda",
    "name": "Responder Ajuda",
    "type": "n8n-nodes-base.httpRequest",
    "typeVersion": 4,
    "position": [900, 100]
}

flow["nodes"].extend([if_comandos_node, ajuda_node, send_ajuda_node])

# Refazer conexões
# Remove the direct link from "Aluno Cadastrado?" -> "AnythingLLM"
aluno_cadastrado_main = flow["connections"]["Aluno Cadastrado?"]["main"]
aluno_cadastrado_main[0] = [{"node": "Se Comando RAG", "type": "main", "index": 0}]

# Add new connections
flow["connections"]["Se Comando RAG"] = {
    "main": [
        [{"node": "AnythingLLM (RAG)", "type": "main", "index": 0}], # true goes to RAG
        [{"node": "Se Comando Ajuda", "type": "main", "index": 0}]   # false goes to Check Ajuda
    ]
}

flow["connections"]["Se Comando Ajuda"] = {
    "main": [
        [{"node": "Responder Ajuda", "type": "main", "index": 0}], # true goes to Ajuda msg
        [{"node": "HTTP 200", "type": "main", "index": 0}]         # false ends (doesn't trigger anything, saving tokens)
    ]
}

flow["connections"]["Responder Ajuda"] = {
    "main": [
        [{"node": "HTTP 200", "type": "main", "index": 0}]
    ]
}

with open(file_path, "w") as f:
    json.dump(flow, f, indent=2)

print("Workflow atualizado com sucesso!")
