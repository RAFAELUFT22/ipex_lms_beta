import { lmsLiteApi } from './lms_lite';

export const evolutionApi = {
  async fetchInstances() {
    return lmsLiteApi.evoFetch();
  },

  async createInstance(params) {
    return lmsLiteApi.evoCreate(params);
  },

  async connectInstance(instanceName) {
    return lmsLiteApi.evoConnect(instanceName);
  },

  async setChatwoot(instanceName, config) {
    return lmsLiteApi.evoSetChatwoot(instanceName, config);
  },

  async deleteInstance(instanceName) {
    return lmsLiteApi.evoDelete(instanceName);
  },

  async sendMessage(instanceName, number, text) {
    return lmsLiteApi.evoSendMessage(instanceName, number, text);
  }
};
