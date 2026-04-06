# econ-graf

Collect OECD country economic indicators into InfluxDB and visualize one dashboard per country in Grafana.

## Data source

The collector uses the free World Bank indicator API (no API key required):

- GDP: `NY.GDP.MKTP.CD`
- Inflation (CPI annual %): `FP.CPI.TOTL.ZG`
- Unemployment (% labor force): `SL.UEM.TOTL.ZS`

Countries covered: OECD members (38 countries).

## Stack

- InfluxDB 2.0
- Grafana
- Python OECD collector (`requests` + `influxdb-client` + `schedule`)

## Prerequisites

- Docker Engine
- Docker Compose v2

Validate installation:

```bash
docker --version
docker compose version
```

## First-time setup

Create the InfluxDB env file expected by `docker-compose.yml`:

```bash
mkdir -p influxdb
cat > influxdb/.env <<'EOF'
INFLUXDB_INIT_MODE=setup
INFLUXDB_INIT_USERNAME=admin
INFLUXDB_INIT_PASSWORD=adminpassword
INFLUXDB_INIT_ORG=oecd_economics
INFLUXDB_INIT_BUCKET=oecd_economic_data
INFLUXDB_INIT_ADMIN_TOKEN=my-super-secret-token
EOF
```

> Note: `.env` files are ignored by git in this repository.

## Run

```bash
docker compose up -d --build
docker compose ps
```

Expected services:

- `influxdb` on `8086`
- `grafana` on `3000`
- `economic_collector`

## Verify (HTTP only)

InfluxDB:

```bash
curl -sS http://localhost:8086/health
```

Grafana:

```bash
curl -sS http://localhost:3000/api/health
```

Dashboards are provisioned (one per OECD country):

```bash
curl -sS -u admin:admin "http://localhost:3000/api/search?query=Economic Dashboard"
```

Collector process:

```bash
docker top economic_collector
```

## Access

- Grafana: http://localhost:3000
  - Username: `admin`
  - Password: `admin`
- InfluxDB: http://localhost:8086

## Logs

```bash
docker compose logs -f
docker logs -f economic_collector
```

## Stop / cleanup

```bash
docker compose down
docker compose down -v
```

## Notes

- Data refresh runs daily at 02:00 UTC after an initial historical load at startup.
- If outbound internet is restricted, the collector may fail to fetch from the World Bank API.