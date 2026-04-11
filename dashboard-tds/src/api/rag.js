import { lmsLiteApi } from './lms_lite';

export const ragApi = {
  async ping() {
    // Basic ping through document list check
    return this.listDocuments();
  },

  async listDocuments() {
    return lmsLiteApi.ragList();
  },

  async uploadDocument(file) {
    return lmsLiteApi.ragUpload(file);
  },

  async query(question) {
    // Note: If chat proxy is needed, we would add it, but for KnowledgeBase management, 
    // we focus on upload/list/delete.
    console.warn("Direct query from frontend is deprecated for security. Use backend routes.");
    return { success: false, message: "Use backend routes" };
  },

  async deleteDocument(docPath) {
    return lmsLiteApi.ragDelete(docPath);
  }
};
