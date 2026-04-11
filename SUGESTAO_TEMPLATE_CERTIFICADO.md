# Suggested Premium HTML Template for N8N (Navy/Gold)

Este template foi projetado para ser usado no nó de envio de e-mail ou geração de PDF do N8N, utilizando as cores oficiais do TDS.

```html
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <title>Certificado Premium TDS</title>
    <style>
        body { font-family: 'Montserrat', sans-serif; background-color: #f8f9fa; margin: 0; padding: 0; }
        .cert-container { 
            width: 800px; height: 600px; margin: 50px auto; 
            border: 20px solid #003366; background: #fff; position: relative;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1); overflow: hidden;
        }
        .cert-container::before {
            content: ""; position: absolute; top: 0; left: 0; right: 0; bottom: 0;
            border: 10px solid #FFCC00; pointer-events: none;
        }
        .header { background-color: #003366; padding: 40px; text-align: center; color: #fff; }
        .header h1 { margin: 0; font-size: 32px; font-family: 'Inter', sans-serif; letter-spacing: 2px; }
        .content { padding: 60px; text-align: center; color: #333; }
        .content h2 { font-size: 24px; color: #003366; }
        .student-name { font-size: 48px; color: #008080; margin: 20px 0; font-weight: bold; border-bottom: 2px solid #FFCC00; display: inline-block; padding: 0 20px; }
        .course-name { font-size: 20px; font-weight: bold; color: #003366; }
        .footer { position: absolute; bottom: 40px; width: 100%; text-align: center; font-size: 14px; }
        .validation-link { color: #003366; text-decoration: none; font-weight: bold; }
        .cert-id { color: #888; margin-top: 10px; }
    </style>
</head>
<body>
    <div class="cert-container">
        <div class="header">
            <h1>CERTIFICADO DE CONCLUSÃO</h1>
        </div>
        <div class="content">
            <p>Certificamos que</p>
            <div class="student-name">{{ student_name }}</div>
            <p>concluiu com êxito o curso de</p>
            <div class="course-name">{{ course }}</div>
            <p>em {{ issue_date }}</p>
        </div>
        <div class="footer">
            <p>Validado por IPEX/UFT e Territórios de Desenvolvimento Social</p>
            <p>Autenticidade garantida em: <br>
                <a href="https://lms.ipexdesenvolvimento.cloud/validate_cert/{{ cert_id }}" class="validation-link">
                    https://lms.ipexdesenvolvimento.cloud/validate_cert/{{ cert_id }}
                </a>
            </p>
            <div class="cert-id">ID: {{ cert_id }}</div>
        </div>
    </div>
</body>
</html>
```

### Explicação do Design:
1. **Azul Marinho (`#003366`)**: Usado no cabeçalho e bordas principais, trazendo seriedade e confiança (Cor UFT/IPEX).
2. **Amarelo Sol/Ouro (`#FFCC00`)**: Usado na borda interna e nos detalhes de destaque, simbolizando inovação e energia.
3. **Teal (`#008080`)**: Cor do nome do aluno, remetendo à natureza e sustentabilidade dos territórios.
4. **Tipografia**: Montserrat para o corpo e Inter para o título, conforme o Plano de Design TDS.
5. **Validação**: Inclui o link real apontando para a API que acabamos de configurar.
