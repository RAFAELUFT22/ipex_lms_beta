import axios from 'axios';

const OPENROUTER_KEY = "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";
const DEFAULT_MODEL = "google/gemini-2.0-flash-lite-001";

export const openRouterApi = {
  summarizeGroups: async (messages) => {
    const prompt = `VOCÊ É O ANALISTA DE GRUPOS TDS. 
    Resuma as mensagens abaixo de forma direta e curta (estilo áudio de 30 segundos).
    Identifique a dúvida principal e dê a melhor solução.

    Mensagens:
    ${messages.map(m => `${m.sender}: ${m.text}`).join('\n')}`;

    const response = await axios.post("https://openrouter.ai/api/v1/chat/completions", {
      model: DEFAULT_MODEL,
      messages: [
        { role: "system", content: "Você é um assistente operacional do Projeto TDS, focado em agilidade e respostas para voz." },
        { role: "user", content: prompt }
      ]
    }, {
      headers: {
        "Authorization": `Bearer ${OPENROUTER_KEY}`,
        "HTTP-Referer": "https://ipexdesenvolvimento.cloud",
        "X-Title": "TDS Admin Dashboard"
      }
    });

    return response.data.choices[0].message.content;
  }
};
