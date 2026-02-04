# Dockerfile für React Frontend
# Multi-Stage Build für optimale Image-Größe

# Build-Stage
FROM node:22-alpine AS builder

# Coolify Build Arguments (werden automatisch von Coolify übergeben)
ARG COOLIFY_URL
ARG COOLIFY_FQDN
ARG DB_DSN
ARG N8N_WEBHOOK_URL
ARG TRAINING_SERVICE_API_URL
ARG COOLIFY_BUILD_SECRETS_HASH

WORKDIR /app

# Dependencies installieren (inkl. devDependencies für Build)
COPY package*.json ./
RUN npm ci

# Source-Code kopieren
COPY . .

# Build für Production
RUN npm run build

# Production-Stage
FROM nginx:alpine

# Coolify Build Arguments (werden automatisch von Coolify übergeben)
ARG COOLIFY_URL
ARG COOLIFY_FQDN
ARG DB_DSN
ARG N8N_WEBHOOK_URL
ARG TRAINING_SERVICE_API_URL
ARG COOLIFY_BUILD_SECRETS_HASH

# Nginx-Konfiguration für React Router
COPY --from=builder /app/dist /usr/share/nginx/html

# Custom Nginx-Konfiguration für SPA mit API-Proxy
RUN echo 'server {\
    listen 3000;\
    server_name localhost;\
    \
    # API-Proxy - alle /api/* Anfragen gehen an Backend\
    location /api/ {\
        proxy_pass http://backend:8000/api/;\
        proxy_set_header Host $host;\
        proxy_set_header X-Real-IP $remote_addr;\
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;\
        proxy_set_header X-Forwarded-Proto $scheme;\
    }\
    \
    # MCP-Proxy - alle /mcp/* Anfragen gehen an Backend (für Claude Code)\
    location /mcp/ {\
        proxy_pass http://backend:8000/mcp/;\
        proxy_set_header Host $host;\
        proxy_set_header X-Real-IP $remote_addr;\
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;\
        proxy_set_header X-Forwarded-Proto $scheme;\
        # SSE-spezifische Einstellungen\
        proxy_set_header Connection \"\";\
        proxy_http_version 1.1;\
        proxy_buffering off;\
        proxy_cache off;\
        proxy_read_timeout 86400s;\
    }\
    \
    # React SPA - alle anderen Anfragen\
    location / {\
        root /usr/share/nginx/html;\
        index index.html index.htm;\
        try_files $uri $uri/ /index.html;\
    }\
}' > /etc/nginx/conf.d/default.conf

EXPOSE 3000

CMD ["nginx", "-g", "daemon off;"]

