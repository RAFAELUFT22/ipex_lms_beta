/**
 * Utility to replace placeholders in strings with values from a student profile object.
 * Supports standard SISEC tags like {name}, {cpf}, {localidade}, {curso}, etc.
 */
export const replaceVariables = (template, profile = {}, course = {}) => {
  if (!template) return "";
  
  const data = {
    name: profile.full_name || "Aluno",
    nome: profile.full_name || "Aluno",
    whatsapp: profile.whatsapp || "",
    cpf: profile.cpf || "não informado",
    localidade: profile.localidade || profile.city || "não informada",
    cidade: profile.localidade || profile.city || "não informada",
    curso: course.title || "TDS",
    data_inscricao: profile.created_at ? new Date(profile.created_at).toLocaleDateString('pt-BR') : "",
    ...profile // Allow dynamic tags from additional profile fields
  };

  return template.replace(/{(\w+)}/g, (match, key) => {
    return data[key] !== undefined ? data[key] : match;
  });
};
