#!/usr/bin/env python3
"""Calculate local RMSE for billing-agent predictions.

Ground-truth CSVs are expected to contain ``order_id`` and ``expected_bill``;
prediction CSVs are expected to contain ``order_id`` and ``Total_Bill``.
Rows are matched by order ID, so their order in the two files does not matter.
"""

from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path
from typing import Iterable, Mapping


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LABELS = PROJECT_ROOT / "data" / "sample_train.csv"
DEFAULT_PREDICTIONS = PROJECT_ROOT / "outputs" / "local_predictions.csv"


def calculate_rmse(actual: Iterable[float], predicted: Iterable[float]) -> float:
    """Return root mean squared error for two equally sized, non-empty series."""
    actual_values = list(actual)
    predicted_values = list(predicted)

    if not actual_values:
        raise ValueError("Cannot calculate RMSE for an empty data set")
    if len(actual_values) != len(predicted_values):
        raise ValueError(
            "Actual and predicted values must have the same length "
            f"({len(actual_values)} != {len(predicted_values)})"
        )
    if not all(math.isfinite(value) for value in actual_values + predicted_values):
        raise ValueError("RMSE inputs must contain only finite numbers")

    mean_squared_error = math.fsum(
        (actual_value - predicted_value) ** 2
        for actual_value, predicted_value in zip(actual_values, predicted_values)
    ) / len(actual_values)
    return math.sqrt(mean_squared_error)


def read_values(path: Path, value_column: str) -> dict[str, float]:
    """Read an order_id-to-value mapping and validate the scoring columns."""
    if not path.is_file():
        raise ValueError(f"CSV file does not exist: {path}")

    with path.open(newline="", encoding="utf-8-sig") as csv_file:
        reader = csv.DictReader(csv_file)
        required = {"order_id", value_column}
        missing_columns = required.difference(reader.fieldnames or [])
        if missing_columns:
            raise ValueError(
                f"{path} is missing required column(s): "
                + ", ".join(sorted(missing_columns))
            )

        values: dict[str, float] = {}
        for line_number, row in enumerate(reader, start=2):
            order_id = (row["order_id"] or "").strip()
            if not order_id:
                raise ValueError(f"{path}:{line_number}: order_id is empty")
            if order_id in values:
                raise ValueError(f"{path}:{line_number}: duplicate order_id {order_id!r}")

            raw_value = (row[value_column] or "").strip()
            try:
                value = float(raw_value)
            except ValueError as error:
                raise ValueError(
                    f"{path}:{line_number}: invalid {value_column} {raw_value!r}"
                ) from error
            if not math.isfinite(value):
                raise ValueError(
                    f"{path}:{line_number}: {value_column} must be finite"
                )
            values[order_id] = value

    if not values:
        raise ValueError(f"{path} contains no data rows")
    return values


def evaluate(
    labels: Mapping[str, float], predictions: Mapping[str, float]
) -> float:
    """Validate order IDs and calculate RMSE in label-file order."""
    missing_ids = labels.keys() - predictions.keys()
    unexpected_ids = predictions.keys() - labels.keys()
    if missing_ids or unexpected_ids:
        details = []
        if missing_ids:
            details.append("missing predictions for: " + ", ".join(sorted(missing_ids)))
        if unexpected_ids:
            details.append("unexpected predictions for: " + ", ".join(sorted(unexpected_ids)))
        raise ValueError("Order IDs do not match (" + "; ".join(details) + ")")

    return calculate_rmse(labels.values(), (predictions[key] for key in labels))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Calculate RMSE between labeled bills and agent predictions."
    )
    parser.add_argument(
        "labels",
        nargs="?",
        type=Path,
        default=DEFAULT_LABELS,
        help=f"labeled CSV (default: {DEFAULT_LABELS.relative_to(PROJECT_ROOT)})",
    )
    parser.add_argument(
        "predictions",
        nargs="?",
        type=Path,
        default=DEFAULT_PREDICTIONS,
        help=(
            "prediction CSV "
            f"(default: {DEFAULT_PREDICTIONS.relative_to(PROJECT_ROOT)})"
        ),
    )
    parser.add_argument("--label-column", default="expected_bill")
    parser.add_argument("--prediction-column", default="Total_Bill")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    try:
        labels = read_values(args.labels, args.label_column)
        predictions = read_values(args.predictions, args.prediction_column)
        rmse = evaluate(labels, predictions)
    except ValueError as error:
        raise SystemExit(f"Error: {error}") from error

    print(f"Rows evaluated: {len(labels)}")
    print(f"RMSE: {rmse:.10g}")


if __name__ == "__main__":
    main()
