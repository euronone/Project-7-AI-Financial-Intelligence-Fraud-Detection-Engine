FROM node:22-alpine AS base

# --- Dependencies ---
FROM base AS deps
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm ci

# --- Builder ---
FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build

# --- Production ---
FROM base AS runner
WORKDIR /app

RUN addgroup --system --gid 1001 finshield && \
    adduser --system --uid 1001 finshield

COPY --from=builder /app/public ./public
COPY --from=builder --chown=finshield:finshield /app/.next/standalone ./
COPY --from=builder --chown=finshield:finshield /app/.next/static ./.next/static

USER finshield

EXPOSE 3000

ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

CMD ["node", "server.js"]
