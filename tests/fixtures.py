from celery import states
from datetime import datetime

class MockVolume:
    def __init__(
        self, name="test-volume", labels=None, mountpoint="/test-volume", options=None
    ) -> None:
        self.name = name
        self.labels = labels or {}
        self.mountpoint = mountpoint
        self.options = options
        self.status = {}
        self.created_at = datetime.fromisoformat("2021-01-01T00:00:00.000000+00:00")


class MockAsyncResult:
    def __init__(self, status=states.PENDING, result="", id="test-task-id") -> None:
        self.status = status
        self.result = result
        self.id = id

