"""16-dim driver / vehicle feature schema used by the edge model.

Index map is fixed so ONNX, tests, and synthetic training stay aligned.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

FEATURE_NAMES = (
    "speed_kph",
    "long_accel_mps2",
    "lat_accel_mps2",
    "yaw_rate_dps",
    "steering_rate_dps",
    "gaze_variance",
    "blink_rate_hz",
    "head_pose_off_forward",
    "phone_use",
    "navi_prompt_rate",
    "hud_item_count",
    "time_to_collision_s",
    "lane_offset_m",
    "cabin_noise_db",
    "hour_of_day",
    "trip_minutes",
)

FEATURE_DIM = len(FEATURE_NAMES)


@dataclass(frozen=True)
class DriverVehicleSample:
    speed_kph: float
    long_accel_mps2: float
    lat_accel_mps2: float
    yaw_rate_dps: float
    steering_rate_dps: float
    gaze_variance: float
    blink_rate_hz: float
    head_pose_off_forward: float
    phone_use: float
    navi_prompt_rate: float
    hud_item_count: float
    time_to_collision_s: float
    lane_offset_m: float
    cabin_noise_db: float
    hour_of_day: float
    trip_minutes: float

    def to_vector(self) -> list[float]:
        return [float(asdict(self)[name]) for name in FEATURE_NAMES]

    @classmethod
    def from_mapping(cls, data: dict) -> "DriverVehicleSample":
        return cls(**{name: float(data[name]) for name in FEATURE_NAMES})


def load_sample(scene_id: str) -> DriverVehicleSample:
    from copilot.process_io import load_scene

    return DriverVehicleSample.from_mapping(load_scene(scene_id)["sample"])
