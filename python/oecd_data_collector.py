import os
import time
from datetime import datetime, timezone

import requests
import schedule
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

# InfluxDB connection parameters
INFLUXDB_URL = os.environ.get("INFLUXDB_URL", "http://influxdb:8086")
INFLUXDB_TOKEN = os.environ.get("INFLUXDB_TOKEN", "my-super-secret-token")
INFLUXDB_ORG = os.environ.get("INFLUXDB_ORG", "oecd_economics")
INFLUXDB_BUCKET = os.environ.get("INFLUXDB_BUCKET", "oecd_economic_data")

WORLD_BANK_API = "https://api.worldbank.org/v2/country/{country}/indicator/{indicator}"

OECD_COUNTRIES = [
    "AUS",
    "AUT",
    "BEL",
    "CAN",
    "CHL",
    "COL",
    "CRI",
    "CZE",
    "DNK",
    "EST",
    "FIN",
    "FRA",
    "DEU",
    "GRC",
    "HUN",
    "ISL",
    "IRL",
    "ISR",
    "ITA",
    "JPN",
    "KOR",
    "LVA",
    "LTU",
    "LUX",
    "MEX",
    "NLD",
    "NZL",
    "NOR",
    "POL",
    "PRT",
    "SVK",
    "SVN",
    "ESP",
    "SWE",
    "CHE",
    "TUR",
    "GBR",
    "USA",
]

INDICATORS = {
    "NY.GDP.MKTP.CD": "GDP (current US$)",
    "FP.CPI.TOTL.ZG": "Inflation, consumer prices (annual %)",
    "SL.UEM.TOTL.ZS": "Unemployment, total (% of total labor force)",
}


def fetch_indicator_data(country_code: str, indicator_code: str) -> list[dict]:
    """Fetch annual economic indicator data from the free World Bank API."""
    response = requests.get(
        WORLD_BANK_API.format(country=country_code, indicator=indicator_code),
        params={"format": "json", "per_page": 20000},
        timeout=30,
    )
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, list) or len(payload) < 2 or not isinstance(payload[1], list):
        return []
    return payload[1]


def fetch_and_store_economic_data():
    """Fetch OECD country indicators and store them in InfluxDB."""
    print(f"Fetching OECD economic data at {datetime.now(timezone.utc).isoformat()}")

    with InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG) as client:
        write_api = client.write_api(write_options=SYNCHRONOUS)
        points = []

        for country_code in OECD_COUNTRIES:
            for indicator_code, indicator_name in INDICATORS.items():
                try:
                    rows = fetch_indicator_data(country_code, indicator_code)
                    valid_rows = 0
                    for row in rows:
                        value = row.get("value")
                        year = row.get("date")
                        if value is None or not year:
                            continue

                        try:
                            timestamp = datetime(int(year), 12, 31, tzinfo=timezone.utc)
                            point = (
                                Point("economic_indicator")
                                .tag("country_code", country_code)
                                .tag("country_name", row.get("country", {}).get("value", country_code))
                                .tag("indicator_code", indicator_code)
                                .tag("indicator_name", indicator_name)
                                .field("value", float(value))
                                .time(timestamp)
                            )
                            points.append(point)
                            valid_rows += 1
                        except (ValueError, TypeError) as parse_error:
                            print(f"Skipping bad row for {country_code}/{indicator_code}: {parse_error}")

                    print(f"{country_code} {indicator_code}: prepared {valid_rows} points")
                except Exception as exc:
                    print(f"Error fetching {country_code}/{indicator_code}: {exc}")

        if points:
            write_api.write(bucket=INFLUXDB_BUCKET, record=points)
            print(f"Wrote {len(points)} OECD economic data points to InfluxDB")
        else:
            print("No economic data points were written in this cycle")


def wait_for_influxdb() -> bool:
    """Wait for InfluxDB to become ready before ingestion."""
    max_retries = 30
    retry_interval = 5

    for i in range(max_retries):
        try:
            with InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG) as client:
                health = client.health()
                if health.status == "pass":
                    print("InfluxDB is ready!")
                    return True
        except Exception as exc:
            print(f"InfluxDB not ready yet: {exc}")

        print(f"Waiting for InfluxDB to be ready... ({i + 1}/{max_retries})")
        time.sleep(retry_interval)

    print("Failed to connect to InfluxDB after multiple retries")
    return False


if __name__ == "__main__":
    if wait_for_influxdb():
        # Load full history immediately and refresh daily.
        fetch_and_store_economic_data()
        schedule.every().day.at("02:00").do(fetch_and_store_economic_data)

        while True:
            schedule.run_pending()
            time.sleep(60)
    else:
        print("Exiting due to InfluxDB connection failure")
