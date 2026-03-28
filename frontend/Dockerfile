# ── Stage 1: Build ────────────────────────────────────────────────────────────
FROM node:20-alpine AS builder

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .

# Inject the production API base URL so Vite bakes it into the bundle.
# nginx proxies /api/* → backend:8000, stripping the /api prefix.
ARG VITE_API_BASE=/api/handshake
ENV VITE_API_BASE=$VITE_API_BASE

RUN npm run build

# ── Stage 2: Serve ────────────────────────────────────────────────────────────
FROM nginx:alpine AS runner

# Copy built assets
COPY --from=builder /app/dist /usr/share/nginx/html

# Custom nginx config (non-root, /api proxy, gzip)
COPY nginx.conf /etc/nginx/nginx.conf

# Allow the nginx user to write temp/pid files
RUN mkdir -p /tmp/client_temp /tmp/proxy_temp /tmp/fastcgi_temp \
             /tmp/uwsgi_temp /tmp/scgi_temp \
    && chown -R nginx:nginx \
        /usr/share/nginx/html \
        /tmp/client_temp /tmp/proxy_temp /tmp/fastcgi_temp \
        /tmp/uwsgi_temp /tmp/scgi_temp

USER nginx

EXPOSE 8080

CMD ["nginx", "-g", "daemon off;"]
