from copilot.driver_state import predict, train_synthetic
from copilot.features import load_sample
from copilot.process_io import load_scene


def test_seeded_training_is_reproducible() -> None:
    a = predict(train_synthetic(seed=7), load_sample("stable"))
    b = predict(train_synthetic(seed=7), load_sample("stable"))
    assert a == b
    assert a.state == load_scene("stable")["expected_state"]
    overload = predict(train_synthetic(seed=7), load_sample("overload"))
    assert overload.state == load_scene("overload")["expected_state"]
