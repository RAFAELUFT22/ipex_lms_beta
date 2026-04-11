import axios from 'axios';

// Get configuration from environment or defaults
const API_BASE_URL = import.meta.env.VITE_ANYTHING_LLM_API_URL || 'https://anything.ipexdesenvolvimento.cloud/api/v1';
const API_TOKEN = import.meta.env.VITE_ANYTHING_LLM_API_KEY || '';
const WORKSPACE_SLUG = import.meta.env.VITE_ANYTHING_LLM_WORKSPACE || 'tds-lms-knowledge';

const ragClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Authorization': `Bearer ${API_TOKEN}`,
    'Content-Type': 'application/json'
  }
});

export const ragApi = {
  // Check if AnythingLLM is reachable
  async ping() {
    try {
      const response = await ragClient.get('/ping');
      return response.data;
    } catch (error) {
      console.error('AnythingLLM Ping Error:', error);
      throw error;
    }
  },

  // List documents in the workspace
  async listDocuments() {
    try {
      const response = await ragClient.get(`/workspace/${WORKSPACE_SLUG}`);
      return response.data.workspace.documents || [];
    } catch (error) {
      console.error('List Documents Error:', error);
      return [];
    }
  },

  // Upload a document and add to workspace
  async uploadDocument(file) {
    const formData = new FormData();
    formData.append('file', file);

    try {
      // 1. Upload to AnythingLLM system
      const uploadRes = await ragClient.post('/document/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      
      const docPath = uploadRes.data.documents[0].location;

      // 2. Map to workspace
      await ragClient.post(`/workspace/${WORKSPACE_SLUG}/update-embeddings`, {
        adds: [docPath]
      });

      return { success: true, docPath };
    } catch (error) {
      console.error('Upload Error:', error);
      throw error;
    }
  },

  // Query the RAG for an answer
  async query(question) {
    try {
      const response = await ragClient.post(`/workspace/${WORKSPACE_SLUG}/chat`, {
        message: question,
        mode: 'query' // 'query' for RAG, 'chat' for session
      });
      return response.data.textResponse;
    } catch (error) {
      console.error('Query Error:', error);
      throw error;
    }
  },

  // Delete a document from workspace
  async deleteDocument(docPath) {
    try {
      await ragClient.post(`/workspace/${WORKSPACE_SLUG}/update-embeddings`, {
        deletes: [docPath]
      });
      return { success: true };
    } catch (error) {
      console.error('Delete Error:', error);
      throw error;
    }
  }
};
