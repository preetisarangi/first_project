#!/usr/bin/env python3
"""Uptime Keep-Alive Verification Script.

Simulates an UptimeRobot HTTP monitor pinging the /health endpoint every 5 minutes
to prevent free-tier cloud hosting (e.g. Render) from spinning down into sleep mode.
Uses only the Python standard library for zero external dependencies.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone


def ping_endpoint(url: str, timeout: float = 10.0) -> bool:
    """Send an HTTP GET request to the target health check URL and report telemetry."""
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "UptimeRobot/2.0 (KeepAlive; +http://www.uptimerobot.com/)",
            "Accept": "application/json",
        },
    )

    now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    start_time = time.perf_counter()

    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            latency_ms = (time.perf_counter() - start_time) * 1000
            status_code = response.getcode()
            body_bytes = response.read()
            body_text = body_bytes.decode("utf-8")

            try:
                data = json.loads(body_text)
                server_status = data.get("status", "unknown")
                server_time = data.get("timestamp", "N/A")
            except Exception:
                server_status = "non-json response"
                server_time = "N/A"

            if status_code == 200 and server_status == "healthy":
                print(
                    f"[{now_utc}] [200 OK] Ping successful ({latency_ms:.1f}ms) "
                    f"| Server Status: '{server_status}' | Server Time: {server_time}"
                )
                return True
            else:
                print(
                    f"[{now_utc}] [WARN {status_code}] Unexpected response ({latency_ms:.1f}ms): {body_text}",
                    file=sys.stderr,
                )
                return False

    except urllib.error.HTTPError as http_err:
        latency_ms = (time.perf_counter() - start_time) * 1000
        print(
            f"[{now_utc}] [FAIL {http_err.code}] HTTP Error ({latency_ms:.1f}ms): {http_err.reason}",
            file=sys.stderr,
        )
        return False
    except urllib.error.URLError as url_err:
        print(f"[{now_utc}] [CONN ERROR] Target unreachable: {url_err.reason}", file=sys.stderr)
        return False
    except Exception as exc:
        print(f"[{now_utc}] [ERROR] Unexpected ping exception: {exc}", file=sys.stderr)
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Simulate UptimeRobot keep-alive monitor targeting /health."
    )
    parser.add_argument(
        "--url",
        "-u",
        default=os.getenv("HEALTH_CHECK_URL", "http://localhost:8000/health"),
        help="Target health check URL (default: http://localhost:8000/health or $HEALTH_CHECK_URL)",
    )
    parser.add_argument(
        "--interval",
        "-i",
        type=int,
        default=300,
        help="Interval between keep-alive pings in seconds (default: 300 / 5 minutes)",
    )
    parser.add_argument(
        "--timeout",
        "-t",
        type=float,
        default=10.0,
        help="Request timeout in seconds (default: 10.0)",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run a single ping check and exit with status code 0 (success) or 1 (failure)",
    )
    args = parser.parse_args()

    print("=" * 70)
    print("  Spec-to-Playwright Engine: Keep-Alive Health Monitor")
    print(f"  Target URL: {args.url}")
    print(f"  Schedule  : {'Single Run (--once)' if args.once else f'Every {args.interval} seconds (5 min standard)'}")
    print("=" * 70)

    if args.once:
        success = ping_endpoint(args.url, timeout=args.timeout)
        sys.exit(0 if success else 1)

    # Continuous pinging loop
    iteration = 1
    try:
        while True:
            print(f"\n[*] Ping #{iteration} starting...")
            ping_endpoint(args.url, timeout=args.timeout)
            print(f"[*] Sleeping for {args.interval} seconds until next keep-alive pulse...")
            time.sleep(args.interval)
            iteration += 1
    except KeyboardInterrupt:
        print("\n[!] Keep-alive monitor stopped by user.")
        sys.exit(0)


if __name__ == "__main__":
    main()

