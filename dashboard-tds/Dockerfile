# Stage 1: Build
FROM node:20-alpine as build
WORKDIR /app
COPY package*.json ./
# Força limpeza para evitar conflitos de cache
RUN npm ci 
COPY . .
# Injeta as URLs de produção em todos os arquivos de API
RUN find src/api -type f -exec sed -i 's|http://localhost:8081|https://api-lms.ipexdesenvolvimento.cloud|g' {} +
RUN find src/api -type f -exec sed -i 's|http://localhost:8000|https://api-lms.ipexdesenvolvimento.cloud|g' {} +
RUN npm run build

# Stage 2: Production
FROM nginx:stable-alpine
# Remove arquivos padrão
RUN rm -rf /usr/share/nginx/html/*
COPY --from=build /app/dist /usr/share/nginx/html
# Configuração Nginx robusta para React Router
COPY <<EOF /etc/nginx/conf.d/default.conf
server {
    listen 80;
    location / {
        root /usr/share/nginx/html;
        index index.html;
        try_files \$uri \$uri/ /index.html;
    }
    # Logs para debug se necessário
    error_log  /var/log/nginx/error.log;
    access_log /var/log/nginx/access.log;
}
EOF
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
