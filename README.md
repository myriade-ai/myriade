<div align="center">
  <img width="128px" src="https://www.myriade.ai/icon.svg" />

# Myriade – Reliable AI analyst for enterprise data warehouses

**Myriade connects to an existing data warehouse, builds the missing context layer, and provides a reliable AI analyst for natural language analytics.**

[Website](https://www.myriade.ai) | [Demo](https://calendly.com/myriade/30min)

</div>

It is designed for real-world data environments: incomplete documentation, unclear schemas, inconsistent metrics, partial dbt coverage, and no semantic layer upfront.

## What it does

- understands warehouse schemas, relationships, metadata, and query history
- integrates with dbt models, metadata, and documentation
- generates and explains SQL
- documents tables, columns, and metrics
- detects data quality issues and anomalies
- grounds answers in source tables, lineage, and checks
- helps data teams review and control AI-generated analysis

## Why

Most AI analytics tools assume the data is already clean, documented, and modeled.

Myriade starts before that.

It builds the context required for reliable analysis directly from the warehouse and the existing data stack, including dbt when available.

The goal is to give companies a trusted AI analyst that can turn enterprise data into useful insights without requiring a semantic layer upfront.

## Installation

Requires Ubuntu 20.04+ or Debian 11+.

```bash
curl -fsSL https://install.myriade.ai | bash
````

Open:

```txt
http://YOUR_SERVER_IP:8080
```

Add SSL:

```bash
sudo /opt/myriade/setup/install_certificate.sh YOUR_DOMAIN.com
```

## Links

* Website: [https://www.myriade.ai](https://www.myriade.ai)
* Demo: [https://calendly.com/myriade/30min](https://calendly.com/myriade/30min)
* Security: [https://www.myriade.ai/security](https://www.myriade.ai/security)
