import axios from 'axios';

const EVOLUTION_URL = "https://evolution.ipexdesenvolvimento.cloud";
const EVOLUTION_API_KEY = "tds_evolution_key_50f5aacc";

export const evolutionApi = {
  createGroup: async (instance, name, description, participants) => {
    const response = await axios.post(`${EVOLUTION_URL}/group/create/${instance}`, {
      subject: name,
      description: description,
      participants: participants
    }, {
      headers: { 'apikey': EVOLUTION_API_KEY }
    });
    return response.data;
  },
  
  sendMessage: async (instance, number, text) => {
    const response = await axios.post(`${EVOLUTION_URL}/message/sendText/${instance}`, {
      number: number,
      text: text
    }, {
      headers: { 'apikey': EVOLUTION_API_KEY }
    });
    return response.data;
  },

  getGroups: async (instance) => {
    const response = await axios.get(`${EVOLUTION_URL}/group/fetchAllGroups/${instance}`, {
      headers: { 'apikey': EVOLUTION_API_KEY }
    });
    return response.data;
  },

  // --- Instance Management ---
  
  createInstance: async (name) => {
    try {
      const response = await axios.post(`${EVOLUTION_URL}/instance/create`, {
        instanceName: name,
        token: "",
        qrcode: true
      }, {
        headers: { 'apikey': EVOLUTION_API_KEY }
      });
      return response.data;
    } catch (e) {
      if (e.response?.status === 400 && e.response?.data?.message?.includes('already exists')) {
        console.warn("Instância já existe, seguindo para conexão...");
        return { instance: { instanceName: name } };
      }
      throw e;
    }
  },

  getInstanceStatus: async (instanceName) => {
    const response = await axios.get(`${EVOLUTION_URL}/instance/connectionStatus/${instanceName}`, {
      headers: { 'apikey': EVOLUTION_API_KEY }
    });
    return response.data;
  },

  fetchInstances: async () => {
    const response = await axios.get(`${EVOLUTION_URL}/instance/fetchInstances`, {
      headers: { 'apikey': EVOLUTION_API_KEY }
    });
    return response.data;
  },

  connectInstance: async (instanceName) => {
    const response = await axios.get(`${EVOLUTION_URL}/instance/connect/${instanceName}`, {
      headers: { 'apikey': EVOLUTION_API_KEY }
    });
    return response.data;
  },

  setChatwoot: async (instanceName, config) => {
    // config should have enabled, accountId, token, url, etc.
    const response = await axios.post(`${EVOLUTION_URL}/chatwoot/set/${instanceName}`, config, {
      headers: { 'apikey': EVOLUTION_API_KEY }
    });
    return response.data;
  },

  deleteInstance: async (instanceName) => {
    const response = await axios.delete(`${EVOLUTION_URL}/instance/delete/${instanceName}`, {
      headers: { 'apikey': EVOLUTION_API_KEY }
    });
    return response.data;
  }
};
