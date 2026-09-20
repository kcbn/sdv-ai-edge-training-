"""Tiny numpy classifier for driver cognitive load. No GPU required."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np

from copilot.features import FEATURE_DIM, DriverVehicleSample

STATE_NAMES = ("stable", "mild_load", "overload_risk")
STATE_JA = ("安定", "軽度負荷", "認知過多予兆")
FEATURE_SCALE = np.array(
    [120.0, 3.0, 3.0, 30.0, 60.0, 1.0, 0.5, 0.7, 1.0, 3.0, 14.0, 12.0, 1.0, 40.0, 24.0, 140.0]
)


class DriverCognitiveLoadPredictor:
    def __init__(self, input_dim: int = FEATURE_DIM, hidden_dim: int = 32, seed: int = 7) -> None:
        rng = np.random.default_rng(seed)
        scale1 = np.sqrt(2.0 / input_dim)
        scale2 = np.sqrt(2.0 / hidden_dim)
        self.w1 = rng.normal(0, scale1, (input_dim, hidden_dim))
        self.b1 = np.zeros(hidden_dim)
        self.w2 = rng.normal(0, scale2, (hidden_dim, hidden_dim))
        self.b2 = np.zeros(hidden_dim)
        self.w3 = rng.normal(0, scale2, (hidden_dim, 3))
        self.b3 = np.zeros(3)

    def logits(self, x: np.ndarray) -> np.ndarray:
        x = x / FEATURE_SCALE
        h = np.maximum(0.0, x @ self.w1 + self.b1)
        h = np.maximum(0.0, h @ self.w2 + self.b2)
        return h @ self.w3 + self.b3


@dataclass(frozen=True)
class DriverStatePrediction:
    state: str
    state_ja: str
    confidence: float
    probabilities: dict[str, float]


def heuristic_label(sample: DriverVehicleSample) -> int:
    risk = 0.0
    risk += 1.4 * sample.phone_use
    risk += 1.1 * min(sample.gaze_variance, 1.0)
    risk += 0.8 * sample.head_pose_off_forward
    risk += 0.6 * min(sample.navi_prompt_rate / 2.0, 1.5)
    risk += 0.4 * min(sample.hud_item_count / 8.0, 1.5)
    if sample.time_to_collision_s < 2.5:
        risk += 1.6
    if abs(sample.lat_accel_mps2) > 1.8:
        risk += 0.7
    if sample.steering_rate_dps > 30:
        risk += 0.5
    if sample.trip_minutes > 90:
        risk += 0.3
    if risk >= 2.4:
        return 2
    if risk >= 1.1:
        return 1
    return 0


def _random_sample(rng: np.random.Generator) -> DriverVehicleSample:
    return DriverVehicleSample(
        speed_kph=float(rng.uniform(0, 120)),
        long_accel_mps2=float(rng.normal(0, 1.2)),
        lat_accel_mps2=float(rng.normal(0, 1.0)),
        yaw_rate_dps=float(abs(rng.normal(2, 8))),
        steering_rate_dps=float(abs(rng.normal(8, 20))),
        gaze_variance=float(rng.uniform(0, 1)),
        blink_rate_hz=float(rng.uniform(0.05, 0.5)),
        head_pose_off_forward=float(rng.uniform(0, 0.7)),
        phone_use=float(rng.integers(0, 2)),
        navi_prompt_rate=float(rng.uniform(0, 3)),
        hud_item_count=float(rng.integers(1, 14)),
        time_to_collision_s=float(rng.uniform(0.8, 12)),
        lane_offset_m=float(abs(rng.normal(0.1, 0.2))),
        cabin_noise_db=float(rng.uniform(50, 80)),
        hour_of_day=float(rng.uniform(0, 23)),
        trip_minutes=float(rng.uniform(1, 140)),
    )


def make_synthetic_batch(n: int = 600, seed: int = 7) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    buckets: dict[int, list[list[float]]] = {0: [], 1: [], 2: []}
    per_class = n // 3
    while min(len(v) for v in buckets.values()) < per_class:
        sample = _random_sample(rng)
        label = heuristic_label(sample)
        if len(buckets[label]) < per_class:
            buckets[label].append(sample.to_vector())
    xs = buckets[0] + buckets[1] + buckets[2]
    ys = [0] * per_class + [1] * per_class + [2] * per_class
    return np.asarray(xs, dtype=np.float64), np.asarray(ys, dtype=np.int64)


def _softmax(logits: np.ndarray) -> np.ndarray:
    z = logits - logits.max(axis=-1, keepdims=True)
    e = np.exp(z)
    return e / e.sum(axis=-1, keepdims=True)


def train_synthetic(epochs: int = 120, seed: int = 7, lr: float = 0.08) -> DriverCognitiveLoadPredictor:
    model = DriverCognitiveLoadPredictor(seed=seed)
    x, y = make_synthetic_batch(seed=seed)
    x_n = x / FEATURE_SCALE
    n = x_n.shape[0]
    eye = np.eye(3)
    for _ in range(epochs):
        h1 = np.maximum(0.0, x_n @ model.w1 + model.b1)
        h2 = np.maximum(0.0, h1 @ model.w2 + model.b2)
        logits = h2 @ model.w3 + model.b3
        probs = _softmax(logits)
        dlogits = (probs - eye[y]) / n
        dw3 = h2.T @ dlogits
        db3 = dlogits.sum(axis=0)
        dh2 = dlogits @ model.w3.T
        dh2 *= h2 > 0
        dw2 = h1.T @ dh2
        db2 = dh2.sum(axis=0)
        dh1 = dh2 @ model.w2.T
        dh1 *= h1 > 0
        dw1 = x_n.T @ dh1
        db1 = dh1.sum(axis=0)
        model.w3 -= lr * dw3
        model.b3 -= lr * db3
        model.w2 -= lr * dw2
        model.b2 -= lr * db2
        model.w1 -= lr * dw1
        model.b1 -= lr * db1
    return model


def predict(model: DriverCognitiveLoadPredictor, sample: DriverVehicleSample) -> DriverStatePrediction:
    logits = model.logits(np.asarray([sample.to_vector()], dtype=np.float64))
    probs = _softmax(logits)[0]
    idx = int(np.argmax(probs))
    return DriverStatePrediction(
        state=STATE_NAMES[idx],
        state_ja=STATE_JA[idx],
        confidence=round(float(probs[idx]), 3),
        probabilities={STATE_NAMES[i]: round(float(probs[i]), 3) for i in range(3)},
    )


def export_onnx(model: DriverCognitiveLoadPredictor, path: Path) -> Path:
    """Optional torch export for CI / edge packaging."""
    import torch
    import torch.nn as nn

    class TorchTwin(nn.Module):
        def __init__(self) -> None:
            super().__init__()
            self.scale = nn.Parameter(torch.tensor(FEATURE_SCALE, dtype=torch.float32), requires_grad=False)
            self.fc1 = nn.Linear(FEATURE_DIM, 32)
            self.fc2 = nn.Linear(32, 32)
            self.fc3 = nn.Linear(32, 3)

        def forward(self, x: torch.Tensor) -> torch.Tensor:
            x = x / self.scale
            x = torch.relu(self.fc1(x))
            x = torch.relu(self.fc2(x))
            return self.fc3(x)

    twin = TorchTwin()
    with torch.no_grad():
        twin.fc1.weight.copy_(torch.tensor(model.w1.T, dtype=torch.float32))
        twin.fc1.bias.copy_(torch.tensor(model.b1, dtype=torch.float32))
        twin.fc2.weight.copy_(torch.tensor(model.w2.T, dtype=torch.float32))
        twin.fc2.bias.copy_(torch.tensor(model.b2, dtype=torch.float32))
        twin.fc3.weight.copy_(torch.tensor(model.w3.T, dtype=torch.float32))
        twin.fc3.bias.copy_(torch.tensor(model.b3, dtype=torch.float32))
    twin.eval()
    path.parent.mkdir(parents=True, exist_ok=True)
    dummy = torch.randn(1, FEATURE_DIM)
    torch.onnx.export(
        twin,
        dummy,
        str(path),
        export_params=True,
        opset_version=14,
        do_constant_folding=True,
        input_names=["driver_vehicle_features"],
        output_names=["load_logits"],
    )
    return path
