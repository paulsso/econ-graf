# econ-graf

Collect FAANG+ stock data into InfluxDB and visualize it in Grafana.

## Stack

- InfluxDB 2.0
- Grafana
- Python stock collector (`yfinance` + `influxdb-client`)

The services are orchestrated with Docker Compose.

## Prerequisites

- Docker Engine
- Docker Compose v2

Validate your install:

```bash
docker --version
docker compose version
```

## First-time setup

1. Clone the repo and enter it.
2. Create the InfluxDB env file expected by `docker-compose.yml`:

```bash
mkdir -p influxdb
cat > influxdb/.env <<'EOF'
INFLUXDB_INIT_MODE=setup
INFLUXDB_INIT_USERNAME=admin
INFLUXDB_INIT_PASSWORD=adminpassword
INFLUXDB_INIT_ORG=faang_stocks
INFLUXDB_INIT_BUCKET=stock_data
INFLUXDB_INIT_ADMIN_TOKEN=my-super-secret-token
EOF
```

> Note: `.env` files are ignored by git in this repository.

## Run the application

Build and start all services:

```bash
docker compose up -d --build
```

Check status:

```bash
docker compose ps
```

Expected services:

- `influxdb` (port `8086`)
- `grafana` (port `3000`)
- `stock_collector`

## Verify environment is working (HTTP-only checks)

InfluxDB health:

```bash
curl -sS http://localhost:8086/health
```

Grafana health:

```bash
curl -sS http://localhost:3000/api/health
```

Grafana dashboard provisioning check:

```bash
curl -sS -u admin:admin "http://localhost:3000/api/search?query=FAANG"
```

Confirm collector process is running:

```bash
docker top stock_collector
```

## Access

- Grafana: http://localhost:3000
  - Username: `admin`
  - Password: `admin`
- InfluxDB: http://localhost:8086

## Logs

Tail all logs:

```bash
docker compose logs -f
```

Collector-only logs:

```bash
docker logs -f stock_collector
```

## Stop / cleanup

Stop services:

```bash
docker compose down
```

Stop services and remove volumes:

```bash
docker compose down -v
```

## Troubleshooting

- If `stock_collector` cannot fetch Yahoo Finance data, your environment may restrict outbound network access.
- If Docker is installed but daemon is not running, start Docker daemon according to your OS setup and retry.