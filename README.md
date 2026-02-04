<div align="center">
  <img width="128px" src="https://www.myriade.ai/icon.svg" />

# Myriade – The AI-Native Data Platform

**Explore, clean, transform, and govern your warehouse with collaborative AI agents.**

[Website](https://www.myriade.ai) | [Live Demo](https://app.myriade.ai)

</div>

---

## Quick Start (try locally)

```bash
docker run -p 8080:8080 -v $(pwd)/data:/app/data myriadeai/myriade:latest
```

Open: [http://localhost:8080](http://localhost:8080)

---

## Production Installation

For production deployments on Ubuntu/Debian servers:

```bash
curl -fsSL https://install.myriade.ai | bash
```

Access your instance at: `http://YOUR_SERVER_IP:8080`

**Add a domain and SSL certificate:**

```bash
sudo /opt/myriade/setup/install_certificate.sh YOUR_DOMAIN.com
```

[Full installation guide](./setup/README.md)

---

## License

See [LICENSE](./LICENSE) for details.
