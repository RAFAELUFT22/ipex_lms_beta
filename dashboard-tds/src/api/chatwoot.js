import axios from 'axios';

const CHATWOOT_URL = "https://chat.ipexdesenvolvimento.cloud";
const CHATWOOT_TOKEN = "w8BYLTQc1s5VMowjQw433rGy";
const ACCOUNT_ID = "1";

const chatwootClient = axios.create({
  baseURL: `${CHATWOOT_URL}/api/v1/accounts/${ACCOUNT_ID}`,
  headers: {
    'api_access_token': CHATWOOT_TOKEN,
    'Content-Type': 'application/json'
  }
});

export const chatwootApi = {
  // Criar uma nova Inbox do tipo API (que a Evolution usa)
  createInbox: async (name) => {
    const response = await chatwootClient.post('/inboxes', {
      name: name,
      channel: {
        type: "api",
        webhook_url: "" // Será preenchido pela Evolution posteriormente
      }
    });
    return response.data;
  },

  // Adicionar um tutor (agente) a uma Inbox específica
  addAgentToInbox: async (inboxId, userId) => {
    const response = await chatwootClient.post('/inbox_members', {
      inbox_id: inboxId,
      user_id: userId
    });
    return response.data;
  },

  // Listar agentes para selecionar qual vincular
  getAgents: async () => {
    const response = await chatwootClient.get('/agents');
    return response.data;
  },

  // Listar Inboxes existentes
  getInboxes: async () => {
    const response = await chatwootClient.get('/inboxes');
    return response.data;
  },

  // Prova de Gestão: Enviar mensagem para o aluno com o Hash do Certificado via Chatwoot
  sendCertificateToStudent: async (phone, courseName, certHash) => {
    // ... (código existente)
  },

  // Automação: Assumir conversa e enviar apresentação oficial do tutor humano
  assignAndGreet: async (phone, agentName = "Suporte TDS") => {
    try {
      // 1. Busca o contato
      const contactRes = await chatwootClient.get(`/contacts/search?q=${encodeURIComponent(phone)}`);
      const contacts = contactRes.data.payload;
      if (!contacts || contacts.length === 0) throw new Error("Contato não encontrado.");
      const contactId = contacts[0].id;

      // 2. Busca a conversa
      const convRes = await chatwootClient.get(`/contacts/${contactId}/conversations`);
      const conversationId = convRes.data.payload[0]?.id;
      if (!conversationId) throw new Error("Nenhuma conversa ativa.");

      // 3. Muda o status para 'Open' (Assumir controle)
      await chatwootClient.post(`/conversations/${conversationId}/toggle_status`, { status: "open" });

      // 4. Envia Apresentação Automática
      const introMsg = `🤝 *Atendimento Humano Ativado*\n\nOlá! Eu sou o Tutor *${agentName}* e assumi sua conversa agora para te dar um suporte especializado.\n\nO Tutor IA foi colocado em modo de espera. Como posso te ajudar hoje?`;
      
      await chatwootClient.post(`/conversations/${conversationId}/messages`, {
        content: introMsg,
        message_type: "outgoing"
      });

      return { status: "success", conversationId };
    } catch (e) {
      throw new Error(`Erro na automação: ${e.message}`);
    }
  },

  // Finalizar atendimento e devolver para o Bot
  resolveAndReturnToBot: async (phone) => {
    try {
      const contactRes = await chatwootClient.get(`/contacts/search?q=${encodeURIComponent(phone)}`);
      const contactId = contactRes.data.payload[0].id;
      const convRes = await chatwootClient.get(`/contacts/${contactId}/conversations`);
      const conversationId = convRes.data.payload[0].id;

      // 1. Resolve no Chatwoot
      await chatwootClient.post(`/conversations/${conversationId}/toggle_status`, { status: "resolved" });

      // 2. Mensagem de Retorno
      const returnMsg = `🤖 *Tutor IA Reativado*\n\nSuporte humano finalizado com sucesso! Estou de volta para continuarmos sua trilha de aprendizado. Vamos lá?`;
      
      await chatwootClient.post(`/conversations/${conversationId}/messages`, {
        content: returnMsg,
        message_type: "outgoing"
      });

      return { status: "success" };
    } catch (e) {
      throw new Error(`Erro ao finalizar: ${e.message}`);
    }
  }
};
