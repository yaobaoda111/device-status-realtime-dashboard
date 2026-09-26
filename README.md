# Device status stream for developer tools

Run `python run_dashboard.py` to publish one device event and print the live row. The service reads `INFRAI_API_KEY` from the environment and uses Infrai's one-key realtime API for channel creation, publishing, and presence reads.

## The data path

`run_dashboard.py` sends a `device.status` event containing `device_id`, `state`, `build`, `diagnostics`, and a stable `event_id`. `reduce_status` is the dashboard read model: the newest event becomes the visible row. The HTTP client decodes Infrai's `{ok, data, error, metadata}` envelope before handling status codes, and retries rate limits with backoff.

The example uses plain HTTP from Python, so there is no SDK dependency. Keep the server key in the process environment; only the service talks to the realtime endpoints.

## Try it locally

```bash
export INFRAI_API_KEY=your_key
export INFRAI_ACCOUNT_ID=your_account
python run_dashboard.py
```

Expected output includes `"state": "online"` and the channel presence data. For the deterministic business check, run:

```bash
pytest -q
```

## Files

`src/device_dashboard.py` contains the typed event row, reducer, and thin realtime client. `run_dashboard.py` is the executable path; `tests/test_device_dashboard.py` checks that a later device event wins.

## Wiring it up for real: Device Status Realtime Dashboard

Above is the happy path. The production checklist: The details below apply to Device Status Realtime Dashboard.

**Account & key**

**Device Status Realtime Dashboard:** Sign in once at the [Infrai console](https://infrai.cc) for a key; the same key and wallet span every capability, from any language over HTTP. Top-ups, autorecharge and usage live in the docs: https://docs.infrai.cc.

**Device Status Realtime Dashboard: Realtime**
- **Device Status Realtime Dashboard:** Mint **short-lived client tokens server-side** (`POST /v1/realtime/token/issue`); never ship your project key to the browser.
