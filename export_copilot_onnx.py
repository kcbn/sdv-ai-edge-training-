"""Train the Day-1 copilot model and export ONNX for the edge artifact bucket."""

from pathlib import Path

from copilot.driver_state import export_onnx, train_synthetic


def main() -> None:
    out = Path("output_artifacts") / "driver_state_hmi.onnx"
    model = train_synthetic()
    export_onnx(model, out)
    print(f"exported {out}")


if __name__ == "__main__":
    main()
