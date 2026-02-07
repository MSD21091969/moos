# Stage 1: Build
FROM node:20-alpine as builder

WORKDIR /app

# Copy package files
COPY package*.json ./
RUN npm ci

# Copy source code
COPY . .

# Build for production
# We inject the VITE_API_URL at build time, but for a real container 
# we might want runtime configuration. For now, we'll bake it in 
# or rely on the .env.production file if it exists.
ARG VITE_API_URL
ENV VITE_API_URL=${VITE_API_URL}
ENV VITE_MODE=cloud

RUN npm run build

# Stage 2: Serve
FROM nginx:alpine

# Copy built assets
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Cloud Run requires listening on port 8080
EXPOSE 8080

CMD ["nginx", "-g", "daemon off;"]
