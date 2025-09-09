# WriteCrew Word Add-in Production Dockerfile
# Multi-stage build for optimized production deployment

# Build stage
FROM node:18-alpine AS builder

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies (including dev dependencies for build)
RUN npm ci --include=dev

# Copy source code
COPY . .

# Build the application
RUN npm run build

# Production stage
FROM nginx:1.25-alpine AS production

# Install additional tools
RUN apk add --no-cache \
    curl \
    jq \
    && rm -rf /var/cache/apk/*

# Copy built application from builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf
COPY nginx-default.conf /etc/nginx/conf.d/default.conf

# Create nginx user and set permissions
RUN addgroup -g 1001 -S nginx-group && \
    adduser -S -D -H -u 1001 -h /var/cache/nginx -s /sbin/nologin -G nginx-group -g nginx nginx-user && \
    chown -R nginx-user:nginx-group /usr/share/nginx/html && \
    chown -R nginx-user:nginx-group /var/cache/nginx && \
    chown -R nginx-user:nginx-group /var/log/nginx && \
    chown -R nginx-user:nginx-group /etc/nginx/conf.d && \
    touch /var/run/nginx.pid && \
    chown -R nginx-user:nginx-group /var/run/nginx.pid

# Switch to non-root user
USER nginx-user

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Expose port
EXPOSE 8080

# Start nginx
CMD ["nginx", "-g", "daemon off;"]

# Labels for metadata
LABEL maintainer="WriteCrew Team <team@writecrew.app>"
LABEL version="1.0.0"
LABEL description="WriteCrew Word Add-in - Multi-Agentic AI Writing Assistant"
LABEL org.opencontainers.image.source="https://github.com/kimhons/ai-writing-platform"
LABEL org.opencontainers.image.documentation="https://docs.writecrew.app"
LABEL org.opencontainers.image.licenses="MIT"

