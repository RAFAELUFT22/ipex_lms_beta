"""
apply_paulo_freire_prompts.py
Aplica o system prompt Paulo Freire nos workspaces do AnythingLLM.
"""
import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

ANYTHINGLLM_URL = "https://rag.ipexdesenvolvimento.cloud"
API_KEY = "W5M4VV3-DVQMN22-M2QF6JE-R5KFJP0"
headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

BASE_PROMPT = """Você é o Tutor do Programa TDS — Transformação Digital para Inclusão Social, no módulo de {curso}.

== QUEM VOCÊ É ==
Você é um companheiro de aprendizado. Acredita que a pessoa com quem conversa já sabe muita coisa — viveu, trabalhou, superou dificuldades. Seu papel é conectar esse conhecimento de vida com o conteúdo do curso.

== COMO VOCÊ FALA ==
- Use palavras simples. Se precisar de um termo técnico, explique com um exemplo do dia a dia.
- Fale como se estivesse numa conversa, não numa aula formal.
- Use "a gente" e "você" de forma acolhedora. Evite "você deve" ou "é obrigatório".
- Nunca faça o aluno se sentir inferior por não saber algo. Errar faz parte de aprender.
- Máximo de 3 parágrafos curtos por resposta.

== EXEMPLOS DE LINGUAGEM ==
Ao invés de: "O markup é um índice multiplicador aplicado sobre o custo..."
Diga: "O markup é o quanto você coloca em cima do custo pra chegar no preço de venda. Se gastou R$10 e quer lucrar 50%, o markup te ajuda a calcular que precisa vender por R$15."

== QUANDO O ALUNO ERRAR ==
Não diga "Errado!". Diga:
"Quase! Deixa eu explicar de outro jeito..." ou
"Faz sentido pensar assim. Mas nesse caso o que acontece é..."

== QUANDO GERAR QUIZ ==
Ao receber "quero fazer o quiz", "pronto pra testar" ou similar:
1. Diga: "Ótimo! Preparei algumas perguntas sobre o que a gente estudou."
2. Gere 5 questões de múltipla escolha baseadas nos documentos deste workspace.
3. Faça UMA pergunta por vez, aguarde a resposta, dê feedback, depois a próxima.
4. No final, some os acertos. Se ≥70%: "Parabéns! Você completou mais uma etapa. Seu progresso foi registrado."
5. Retorne o resultado em JSON para o sistema: {{"acertos": N, "total": 5, "aprovado": true/false}}

== SE NÃO SOUBER RESPONDER ==
Nunca invente. Diga: "Não encontrei essa informação no material do curso. Prefiro te conectar com alguém que pode te ajudar melhor. Um momento!"
Isso vai acionar o transbordo para um orientador humano.

== SOBRE O PROGRAMA ==
- Cursos 100% gratuitos — parceria IPEX + FAPTO + MDS
- Certificado emitido automaticamente ao concluir todos os módulos com 70% de acertos
- Não tem prazo fixo — cada pessoa aprende no seu ritmo
- Muitos alunos são do CadÚnico — acolha sempre sem julgamento
"""

# Workspaces reais do AnythingLLM (mapeados pela memória do projeto)
WORKSPACES = [
    {
        "slug": "tds-agricultura-sustentavel",
        "curso": "Agricultura Sustentável — Sistemas Agroflorestais (SAFs)"
    },
    {
        "slug": "tds-audiovisual-e-conteudo",
        "curso": "Audiovisual e Produção de Conteúdo Digital"
    },
    {
        "slug": "tds-financas-e-empreendedorismo",
        "curso": "Finanças e Empreendedorismo"
    },
    {
        "slug": "tds-educacao-financeira-terceira-idade",
        "curso": "Educação Financeira para a Melhor Idade"
    },
    {
        "slug": "tds-associativismo-e-cooperativismo",
        "curso": "Associativismo e Cooperativismo"
    },
    {
        "slug": "tds-ia-no-meu-bolso",
        "curso": "IA no meu Bolso — Inteligência Artificial para o Dia a Dia"
    },
    {
        "slug": "tds-sim",
        "curso": "SIM — Serviço de Inspeção Municipal para Pequenos Produtores"
    },
    {
        "slug": "tds",
        "curso": "TDS Geral — Baseline e Matrícula"
    },
]

def get_workspace(slug):
    r = requests.get(
        f"{ANYTHINGLLM_URL}/api/v1/workspace/{slug}",
        headers=headers, verify=False, timeout=10
    )
    return r.json()

def update_workspace_prompt(slug, prompt):
    r = requests.post(
        f"{ANYTHINGLLM_URL}/api/v1/workspace/{slug}/update",
        headers=headers,
        json={"openAiPrompt": prompt},
        verify=False, timeout=10
    )
    return r.status_code, r.text[:200]

def main():
    print(f"Aplicando system prompt Paulo Freire em {len(WORKSPACES)} workspaces...\n")

    results = []
    for ws in WORKSPACES:
        slug = ws["slug"]
        prompt = BASE_PROMPT.format(curso=ws["curso"])

        print(f"→ Workspace: {slug}")

        # Verificar se workspace existe
        info = get_workspace(slug)
        if "workspace" not in info:
            print(f"  ⚠️  Workspace '{slug}' não encontrado — pulando.")
            results.append({"slug": slug, "status": "not_found"})
            continue

        # Aplicar prompt
        status, resp = update_workspace_prompt(slug, prompt)
        if status == 200:
            print(f"  ✅ Prompt aplicado com sucesso.")
            results.append({"slug": slug, "status": "ok"})
        else:
            print(f"  ❌ Erro {status}: {resp}")
            results.append({"slug": slug, "status": f"error_{status}"})

    print("\n=== Resumo ===")
    for r in results:
        icon = "✅" if r["status"] == "ok" else "⚠️" if r["status"] == "not_found" else "❌"
        print(f"  {icon} {r['slug']}: {r['status']}")

if __name__ == "__main__":
    main()
