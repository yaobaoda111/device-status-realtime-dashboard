from src.device_dashboard import reduce_status


def test_latest_device_event_drives_dashboard_row():
    events = [
        {"device_id": "dev-7", "state": "booting", "build": "41", "diagnostics": "checking"},
        {"device_id": "dev-7", "state": "online", "build": "42", "diagnostics": "clean"},
    ]
    assert reduce_status(events).state == "online"
    assert reduce_status(events).build == "42"
