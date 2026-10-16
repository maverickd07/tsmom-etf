"""Chronological walk-forward splits with disjoint evaluation windows."""

from dataclasses import dataclass
from datetime import date
from typing import Iterable, List


@dataclass(frozen=True)
class WalkForwardSplit:
    train: slice
    test: slice


def walk_forward_splits(
    dates: Iterable[date], train_size: int, test_size: int,
    gap: int = 0, expanding: bool = False,
) -> List[WalkForwardSplit]:
    """Return half-open row slices for complete chronological test blocks.

    Training always precedes testing. Gap excludes rows immediately before
    each test block. Test blocks never overlap; incomplete final blocks are
    omitted. Rolling training has train_size rows; expanding training starts
    at row zero and uses train_size as its initial size. No model is fit here.
    """
    for name, value, minimum in (("train_size", train_size, 1),
                                 ("test_size", test_size, 1), ("gap", gap, 0)):
        if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
            raise ValueError(name + " has an invalid size")
    if not isinstance(expanding, bool):
        raise ValueError("expanding must be a boolean")
    ordered = list(dates)
    if any(type(day) is not date for day in ordered):
        raise ValueError("dates must be daily date objects")
    if any(b <= a for a, b in zip(ordered, ordered[1:])):
        raise ValueError("dates must strictly increase without duplicates")
    splits = []
    for start in range(train_size + gap, len(ordered) - test_size + 1, test_size):
        train_stop = start - gap
        train_start = 0 if expanding else train_stop - train_size
        splits.append(WalkForwardSplit(slice(train_start, train_stop),
                                       slice(start, start + test_size)))
    return splits
