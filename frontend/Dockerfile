# Imagem do frontend Esporte+ — build Vite servido por nginx (multi-stage)

# --------- Etapa 1: build ---------
FROM node:20-alpine AS build

WORKDIR /app

# VITE_API_URL é embutido no bundle em tempo de build (Vite substitui
# import.meta.env.VITE_API_URL na compilação); precisa ser a URL PÚBLICA da API,
# acessível pelo navegador. Obrigatório: sem ele o build falha (vite.config.js).
#   docker build --build-arg VITE_API_URL=https://api.seudominio.com .
ARG VITE_API_URL
ENV VITE_API_URL=${VITE_API_URL}

COPY package.json package-lock.json* ./
RUN npm ci

COPY index.html vite.config.js ./
COPY src ./src

RUN npm run build

# --------- Etapa 2: runtime (nginx servindo o SPA) ---------
FROM nginx:1.27-alpine

COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
