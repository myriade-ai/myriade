<div align="center">
  <img width="128px" src="https://www.myriade.ai/icon.svg" />

# Myriade – The AI-Native Data Platform

**Explore, clean, transform, and govern your warehouse with collaborative AI agents.**

[Website](https://www.myriade.ai) | [Live Demo](https://app.myriade.ai)

</div>

---

## Quick Start (Docker)

**With SQLite backend (simplest)**

```bash
docker run -p 8080:8080 -v $(pwd)/data:/app/data myriadeai/myriade:latest
```

Open: [http://localhost:8080](http://localhost:8080)

**With PostgreSQL backend**

```bash
docker run -p 8080:8080 \
  -e DATABASE_URL=postgresql://<db_user>:<strong_password>@localhost:5432/myriade \
  myriadeai/myriade:latest
```

> Always use dedicated, non-default credentials.

---

## Docker Compose

For a complete setup with PostgreSQL, use the provided `docker-compose.yml`:

```bash
# Set required environment variable
export POSTGRES_PASSWORD=your_secure_password

# Start services
docker compose up -d
```

Open: [http://localhost:8080](http://localhost:8080)

Optional environment variables:
- `HOST` - Public URL for OAuth callbacks (e.g., `https://myriade.example.com`)

---

## Production Installation

For production deployments on Ubuntu/Debian servers:

```bash
curl -fsSL https://install.myriade.ai | bash
```

This installs Docker, PostgreSQL, and starts Myriade on port 8080.

**Add a domain and SSL certificate:**

```bash
sudo /opt/myriade/setup/install_certificate.sh YOUR_DOMAIN.com
```

[Full installation guide](./setup/README.md)

---

## License

See [LICENSE](./LICENSE) for details.
