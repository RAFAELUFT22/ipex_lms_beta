import json
import sys

def anonymize_sisec(student_data):
    """
    Remove PII (Personally Identifiable Information) from SISEC data
    while keeping the educational and socio-economic context for the IA.
    Suporta os 102 campos oficiais do projeto TDS.
    """
    # Lista de campos que contém PII e devem ser EXCLUÍDOS
    pii_fields = [
        "campo_6",      # Nome Completo
        "campo_9",      # CPF
        "campo_10",     # RG
        "campo_16",     # Telefone (já enviado via ID/WhatsApp separado)
        "campo_17",     # E-mail
        "campo_18",     # Logradouro
        "campo_19",     # Número (Endereço)
        "campo_assinatura", # Assinatura
        "full_name",
        "email",
        "phone",
        "cpf"
    ]
    
    context = {}
    for key, value in student_data.items():
        # Incluir apenas se não for PII e tiver valor útil
        if key not in pii_fields and value and value != "N/A":
            context[key] = value
            
    return context

if __name__ == "__main__":
    try:
        data = json.load(sys.stdin)
        anonymized = anonymize_sisec(data)
        print(json.dumps(anonymized, indent=2, ensure_ascii=False))
    except Exception as e:
        print(json.dumps({"error": str(e)}))
