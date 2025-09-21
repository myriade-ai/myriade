# Multi-stage build for single container Myriade deployment
FROM node:lts-alpine AS frontend-build

# Build Vue.js frontend
WORKDIR /app/view
COPY view/package.json view/yarn.lock ./
ENV NODE_OPTIONS="--max_old_space_size=4096"
RUN yarn install

COPY view/ .
RUN yarn build

# Main application stage
FROM python:3.11.4

# Set working directory
WORKDIR /app

# Install system dependencies and Node.js (for echarts-render)
RUN apt-get update && apt-get install -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js for echarts-render
ENV NODE_VERSION=20.19.0
RUN curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.5/install.sh | bash
ENV NVM_DIR=/root/.nvm
RUN . "$NVM_DIR/nvm.sh" && nvm install $NODE_VERSION
RUN . "$NVM_DIR/nvm.sh" && nvm use v$NODE_VERSION
RUN . "$NVM_DIR/nvm.sh" && nvm alias default v$NODE_VERSION
ENV PATH="/root/.nvm/versions/node/v$NODE_VERSION/bin/:${PATH}"
RUN npm install -g yarn

# Copy service files
COPY service/ .

# Install echarts-render dependencies
COPY service/chat/tools/echarts-render ./chat/tools/echarts-render
RUN cd chat/tools/echarts-render && yarn

# Install Python dependencies
RUN pip install uv
COPY service/pyproject.toml service/uv.lock ./
RUN uv sync --all-extras

# Copy built frontend files to Flask static folder
COPY --from=frontend-build /app/view/dist ./static

# Create data directory for SQLite (when using docker run)
RUN mkdir -p /app/data

# Create log directory for gunicorn
RUN mkdir -p /var/log/gunicorn

# Copy environment file for Docker
COPY .env.docker .env

# Set static folder path for single container
ENV STATIC_FOLDER=./static

# Expose port 8080 (avoids conflicts with other services)
EXPOSE 8080

# Run the application
CMD ["bash", "start.sh", "prod"]