import { lmsLiteApi } from './lms_lite';

export const chatwootApi = {
  // Search for a contact by phone/identifier
  async searchContact(query) {
    return lmsLiteApi.cwSearch(query);
  },

  // Get active conversations for a contact
  async getContactConversations(contactId) {
    return lmsLiteApi.cwGetConvs(contactId);
  },

  // Simplified Handoff: Assign contact, send presentation, and pause IA
  async assignAndGreet(contactId, tutorName) {
    try {
      // 1. Get Conversation
      const convs = await this.getContactConversations(contactId);
      if (!convs || convs.length === 0) throw new Error("No active conversation found");
      const convId = convs[0].id;

      // 2. Pause IA (Toggle Status to 'pending' or similar trigger)
      // In TDS, human takeover often means changing status or adding a 'takeover' label
      await lmsLiteApi.cwToggleStatus(convId, "open"); // Ensure it's open for human
      
      // 3. Send Hello Message from Tutor
      const msg = `Olá! Sou o ${tutorName}, seu tutor sênior. Vou assumir este atendimento para te ajudar com detalhes mais complexos. Como posso ajudar?`;
      await lmsLiteApi.cwSendMsg(convId, msg);

      return { success: true, convId };
    } catch (error) {
      console.error("Handoff Error:", error);
      throw error;
    }
  },

  // Terminate handoff and return to IA
  async resolveAndReturn(convId) {
    return lmsLiteApi.cwToggleStatus(convId, "resolved");
  },

  // Create inbox for a tutor
  async createInbox(name) {
    return lmsLiteApi.cwCreateInbox(name);
  }
};
