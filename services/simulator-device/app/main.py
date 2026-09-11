"""Initial simulator placeholder. It intentionally sends no data until telemetry contracts exist."""

import os
import time


def main() -> None:
    telemetry_url = os.getenv("TELEMETRY_URL", "http://telemetry-service:8000/health")
    print(f"LabWatch simulator ready. Telemetry target: {telemetry_url}", flush=True)
    while True:
        time.sleep(60)


if __name__ == "__main__":
    main()
