import hashlib

TDS_SECRET = "TDS_SECRET_2026"

def generate_cert_hash(whatsapp, course_slug):
    """
    Gera um hash SHA-256 baseado no WhatsApp do aluno, slug do curso e um segredo.
    Retorna os primeiros 12 caracteres do hash hexadecimal.
    """
    data = f"{whatsapp}:{course_slug}:{TDS_SECRET}"
    hash_obj = hashlib.sha256(data.encode())
    full_hash = hash_obj.hexdigest()
    return full_hash[:12]

if __name__ == "__main__":
    # Teste rápido
    print(generate_cert_hash("5563999374165", "audiovisual-e-produ-o-de-conte-do-digital-2"))
