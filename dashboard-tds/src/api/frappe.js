import axios from 'axios';

const FRAPPE_URL = "https://lms.ipexdesenvolvimento.cloud";
const FRAPPE_API_KEY = "056681de29fce7a";
const FRAPPE_SECRET = "7c78dcba6e3c5d1";

export const frappeApi = {
  getStudentInfo: async (whatsapp) => {
    // Simulation: Mock for the specific number requested
    if (whatsapp === "5563999374165") {
      return {
        full_name: "RAFAEL TESTE SISEC",
        campo_6: "RAFAEL TESTE SISEC",
        campo_23: "Palmas - TO",
        campo_25: "Médio completo",
        campo_29: "Não",
        campo_31: "Sim", // Inscrito no CadÚnico
        campo_40: "Sim", // Trabalhador rural
        campo_41: "Não", // Pescador
        campo_58: "R$ 601 a R$ 1.200", 
        campo_62: "Sim", 
        campo_63: "Horticultura Orgânica",
        campo_99: "Aprender a vender melhor meus produtos",
        campo_cadunico_verificado: "Inscrito"
      };
    }

    // Note: in Frappe, we filter by the 'whatsapp' field in the 'TDS Aluno' doctype
    const response = await axios.get(`${FRAPPE_URL}/api/resource/TDS Aluno`, {
      params: {
        filters: JSON.stringify([["whatsapp", "=", whatsapp]]),
        fields: JSON.stringify(["*"])
      },
      headers: {
        "Authorization": `token ${FRAPPE_API_KEY}:${FRAPPE_SECRET}`
      }
    });
    return response.data.data[0] || null;
  }
};
