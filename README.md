# econ-graf

Collect OECD country economic indicators into InfluxDB and visualize one dashboard per country in Grafana.

## Data source

The collector uses the free World Bank indicator API (no API key required):

- GDP: `NY.GDP.MKTP.CD`
- Inflation (CPI annual %): `FP.CPI.TOTL.ZG`
- Unemployment (% labor force): `SL.UEM.TOTL.ZS`

Countries covered: OECD members (38 countries).

## Stack

- InfluxDB 2.0 (`oecd_economics` org, `oecd_economic_data` bucket)
- Grafana 11.6 (provisioned InfluxDB datasource UID `influxdb-oecd`)
- Python OECD collector (`requests` + `influxdb-client` + `schedule`)

## Prerequisites

- Docker Engine
- Docker Compose v2

```bash
docker --version
docker compose version
```

## Run

```bash
docker compose up -d --build
docker compose ps
```

Expected services:

- `influxdb` on `8086`
- `grafana` on `3000`
- `oecd_collector`

If Grafana was previously started with an older datasource config, reset its volume so provisioning can recreate the datasource UID:

```bash
docker compose down
docker volume rm workspace_grafana-data
docker compose up -d --build
```

## Verify

InfluxDB:

```bash
curl -sS http://localhost:8086/health
```

Grafana:

```bash
curl -sS http://localhost:3000/api/health
```

Datasource UID must be `influxdb-oecd`:

```bash
curl -sS -u admin:admin http://localhost:3000/api/datasources \
  | python3 -c "import json,sys; print([(d['name'], d['uid']) for d in json.load(sys.stdin)])"
```

Dashboards (one per OECD country):

```bash
curl -sS -u admin:admin "http://localhost:3000/api/search?query=Economic Dashboard"
```

## Access

- Grafana: http://localhost:3000
  - Username: `admin`
  - Password: `admin`
- InfluxDB: http://localhost:8086

Open **OECD** in the Grafana sidebar and pick a country dashboard. The default time range is the last 30 years.

## Logs

```bash
docker compose logs -f
docker logs -f oecd_collector
```

## Stop / cleanup

```bash
docker compose down
docker compose down -v
```

## Notes

- Data refresh runs daily at 02:00 UTC after an initial historical load at startup.
- If outbound internet is restricted, the collector may fail to fetch from the World Bank API.
- Country dashboards query the InfluxDB datasource by UID `influxdb-oecd`. If panels are empty, confirm that UID exists in Grafana Connections → Data sources.
