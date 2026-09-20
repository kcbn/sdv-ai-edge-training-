import time

from copilot.driver_state import predict, train_synthetic
from copilot.features import load_sample


def test_state_inference_under_10ms() -> None:
    model = train_synthetic()
    sample = load_sample("overload")
    predict(model, sample)
    started = time.perf_counter()
    for _ in range(200):
        predict(model, sample)
    elapsed_ms = (time.perf_counter() - started) * 1000 / 200
    assert elapsed_ms < 10.0, f"mean latency {elapsed_ms:.3f} ms"
