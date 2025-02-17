# Use an official lightweight Python image
FROM python:3.11.4

# Set the working directory in the container
WORKDIR /app

# Install system dependencies (if any)
RUN apt-get update && apt-get install -y --no-install-recommends

# Install uv package installer
RUN pip install uv

# Copy poetry.lock and pyproject.toml
COPY ./pyproject.toml ./uv.lock ./

## Install Python dependencies using uv sync
# RUN uv sync --locked --no-dev

RUN uv pip compile pyproject.toml > requirements.txt
RUN uv pip install --system -r requirements.txt

# Install Playwright and its dependencies
RUN uv pip install --system playwright
# RUN playwright install chromium
# RUN playwright install-deps chromium

RUN uv pip install --system clerk_backend_api

# Copy the rest of the application's code
COPY . .

# Inform Docker that the container listens on the specified port at runtime.
EXPOSE 4000

RUN ls -la /app

# Define the command to run the Flask application
CMD ["bash", "run.sh"]
