# Multi-stage build for Next.js frontend optimized for AWS deployment
# Stage 1: Install dependencies
FROM node:20-alpine as deps

WORKDIR /app

# Copy package manifests
COPY package.json package-lock.json* yarn.lock* pnpm-lock.yaml* ./

# Install dependencies (both prod and dev, needed for build)
RUN if [ -f "pnpm-lock.yaml" ]; then \
        npm install -g pnpm && pnpm install --frozen-lockfile; \
    elif [ -f "yarn.lock" ]; then \
        yarn install --frozen-lockfile; \
    else \
        npm ci; \
    fi

# Stage 2: Builder
FROM node:20-alpine as builder

WORKDIR /app

ENV NEXT_TELEMETRY_DISABLED=1

# Copy node_modules from deps stage
COPY --from=deps /app/node_modules ./node_modules

# Copy application source
COPY . .

# Build Next.js application with environment variables
# Environment variables are injected at build time via Docker
RUN npm run build || yarn build || pnpm build

# Stage 3: Production runtime
FROM node:20-alpine as runtime

WORKDIR /app

ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1 \
    PORT=3000 \
    HOSTNAME=0.0.0.0

# Install only production runtime dependencies
RUN apk add --no-cache curl dumb-init

# Create non-root user for security (required for AWS)
RUN addgroup -g 1001 -S nodejs && \
    adduser -S nextjs -u 1001

# Copy built application from builder
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/package*.json ./

# Fix permissions
RUN chown -R nextjs:nodejs /app

USER nextjs

EXPOSE 3000

# Health check (curl is available)
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:3000/api/health || exit 1

# Use dumb-init to handle signals properly in containers
ENTRYPOINT ["/usr/bin/dumb-init", "--"]

# Start Next.js application
CMD ["node", "server.js"]
