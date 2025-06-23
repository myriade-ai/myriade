# Use an official lightweight Python image
FROM python:3.11.4

# Set the working directory in the container
WORKDIR /app

# Install system dependencies (if any)
RUN apt-get update && apt-get install -y --no-install-recommends

## == Echarts render ==
# Install node
ENV NODE_VERSION=20.19.0
RUN curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.5/install.sh | bash
ENV NVM_DIR=/root/.nvm
RUN . "$NVM_DIR/nvm.sh" && nvm install $NODE_VERSION
RUN . "$NVM_DIR/nvm.sh" && nvm use v$NODE_VERSION
RUN . "$NVM_DIR/nvm.sh" && nvm alias default v$NODE_VERSION
ENV PATH="/root/.nvm/versions/node/v$NODE_VERSION/bin/:${PATH}"
RUN npm install -g yarn

# Install dependencies
COPY ./chat/tools/echarts-render ./chat/tools/echarts-render
RUN cd chat/tools/echarts-render && yarn
## End of Echarts render

# Install uv package installer
RUN pip install uv

# Copy uv.lock and pyproject.toml
COPY ./pyproject.toml ./uv.lock ./

## Install Python dependencies using uv sync
RUN uv sync --locked --all-extras


# Copy the rest of the application's code
COPY . .

# Inform Docker that the container listens on the specified port at runtime.
EXPOSE 4000

RUN ls -la /app

# Define the command to run the Flask application
CMD ["bash", "start.sh", "prod"]
