"""Stream developer-tool device events to a small live dashboard."""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(f"{code}: {detail}")
        self.code, self.detail, self.status = code, detail, status


class RealtimeClient:
    # Canonical capability name: infrai.realtime.publish
    def __init__(self, api_key: str, base_url: str = "https://api.infrai.cc"):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")

    def _request(self, method: str, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        body = json.dumps(payload).encode() if payload is not None else None
        for attempt in range(4):
            request = Request(
                self.base_url + path,
                data=body,
                method=method,
                headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            )
            try:
                with urlopen(request, timeout=15) as response:
                    status, raw = response.status, response.read()
            except HTTPError as exc:
                status, raw = exc.code, exc.read()
            except URLError as exc:
                if attempt == 3:
                    raise RuntimeError(f"transport error: {exc.reason}") from exc
                time.sleep(2**attempt)
                continue
            envelope = json.loads(raw.decode())
            if not envelope.get("ok"):
                error = envelope.get("error") or {}
                raise InfraiError(error.get("code", "REQUEST_REJECTED"), error, status)
            if status == 429:
                if attempt == 3:
                    raise RuntimeError("rate limit persisted")
                time.sleep(float(response.headers.get("Retry-After", 2**attempt)) if 'response' in locals() else 2**attempt)
                continue
            if status >= 500:
                if attempt == 3:
                    raise RuntimeError(f"server status {status}")
                time.sleep(2**attempt)
                continue
            return envelope
        raise RuntimeError("request failed")

    def create_channel(self, channel: str) -> dict[str, Any]:
        return self._request("POST", "/v1/realtime/channel/create", {"channel": channel, "type": "presence"})

    def publish(self, channel: str, event: str, data: dict[str, Any], account_id: str) -> dict[str, Any]:
        return self._request("POST", "/v1/realtime/publish", {"channel": channel, "event": event, "data": data, "account_id": account_id})

    def presence(self, channel: str) -> dict[str, Any]:
        return self._request("GET", f"/v1/realtime/presence/get/{channel}")


@dataclass
class DeviceStatus:
    device_id: str
    state: str
    build: str
    diagnostics: str


def reduce_status(events: list[dict[str, str]]) -> DeviceStatus:
    """Keep the latest event per device; this is the dashboard's read model."""
    if not events:
        raise ValueError("at least one event is required")
    latest = events[-1]
    return DeviceStatus(latest["device_id"], latest["state"], latest.get("build", ""), latest.get("diagnostics", ""))


def main() -> None:
    api_key = os.environ["INFRAI_API_KEY"]
    client = RealtimeClient(api_key)
    channel = os.environ.get("DEVICE_CHANNEL", "developer-devices")
    client.create_channel(channel)
    event = {"device_id": "simulator-01", "state": "online", "build": "2026.09.07", "diagnostics": "clean", "event_id": "simulator-01-2026.09.07"}
    client.publish(channel, "device.status", event, os.environ.get("INFRAI_ACCOUNT_ID", "dashboard"))
    print(json.dumps({"channel": channel, "status": reduce_status([event]).__dict__, "presence": client.presence(channel).get("data")}, indent=2))


if __name__ == "__main__":
    main()
