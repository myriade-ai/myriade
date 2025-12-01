# Multi-stage build for single container Myriade deployment

# Stage 1: Build Vue.js frontend
FROM node:lts-alpine AS frontend-build

WORKDIR /app/view
COPY view/package.json view/yarn.lock ./
ENV NODE_OPTIONS="--max_old_space_size=4096"
RUN yarn install

COPY view/ .
RUN yarn build:prod

# Stage 2: Main application
FROM python:3.11.4

WORKDIR /app

# Install system dependencies (rarely changes - cached)
RUN apt-get update && apt-get install -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js for echarts-render (rarely changes - cached)
ENV NODE_VERSION=20.19.0
RUN curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.5/install.sh | bash
ENV NVM_DIR=/root/.nvm
RUN . "$NVM_DIR/nvm.sh" && nvm install $NODE_VERSION
RUN . "$NVM_DIR/nvm.sh" && nvm use v$NODE_VERSION
RUN . "$NVM_DIR/nvm.sh" && nvm alias default v$NODE_VERSION
ENV PATH="/root/.nvm/versions/node/v$NODE_VERSION/bin/:${PATH}"
RUN npm install -g yarn

# Install Python dependencies first (only changes when pyproject.toml/uv.lock change)
RUN pip install uv
COPY service/pyproject.toml service/uv.lock ./
RUN uv sync --all-extras

# Install echarts-render dependencies (only changes when its package.json changes)
COPY service/chat/tools/echarts-render/package.json service/chat/tools/echarts-render/yarn.lock* ./chat/tools/echarts-render/
RUN cd chat/tools/echarts-render && yarn install

# Copy echarts-render source files
COPY service/chat/tools/echarts-render ./chat/tools/echarts-render

# Copy backend source code (changes frequently - at the end)
COPY service/ .

# Copy built frontend files (independent of backend layers)
COPY --from=frontend-build /app/view/dist ./static

# Create directories
RUN mkdir -p /app/data /var/log/gunicorn

# Copy environment file for Docker
COPY .env.docker .env

# Set static folder path for single container
ENV STATIC_FOLDER=./static

# Expose port 8080
EXPOSE 8080

# Run the application
CMD ["bash", "start.sh", "prod"]
