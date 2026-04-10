"""디텍션 수신 시 적용하는 신뢰도·등록 간격 설정."""

from __future__ import annotations

import asyncio
import os
import time
from dataclasses import dataclass


def _parse_confidence_threshold() -> float:
    raw = os.getenv("DETECTION_CONFIDENCE_THRESHOLD", "0.25").strip()
    try:
        return float(raw)
    except ValueError:
        return 0.25


def _parse_min_interval_seconds() -> float:
    raw = os.getenv("DETECTION_MIN_INTERVAL_SECONDS", "0").strip()
    try:
        return max(0.0, float(raw))
    except ValueError:
        return 0.0


@dataclass(frozen=True)
class DetectionIntakeSettings:
    min_confidence: float
    min_interval_seconds: float


def load_detection_intake_settings() -> DetectionIntakeSettings:
    return DetectionIntakeSettings(
        min_confidence=_parse_confidence_threshold(),
        min_interval_seconds=_parse_min_interval_seconds(),
    )


def normalize_detection_score(raw: object) -> float:
    if raw is None:
        return 0.0
    try:
        return float(raw)
    except (TypeError, ValueError):
        return 0.0


class DetectionIntervalGate:
    """camera_id별 최소 등록 간격(서버 메모리, 프로세스 단위)."""

    def __init__(self, min_interval_seconds: float) -> None:
        self._min_interval = min_interval_seconds
        self._lock = asyncio.Lock()
        self._last_monotonic_by_camera: dict[int, float] = {}

    async def claim(self, camera_id: int) -> bool:
        if self._min_interval <= 0:
            return True
        now = time.monotonic()
        async with self._lock:
            last = self._last_monotonic_by_camera.get(camera_id)
            if last is not None and (now - last) < self._min_interval:
                return False
            self._last_monotonic_by_camera[camera_id] = now
            return True
