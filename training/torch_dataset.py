from __future__ import annotations

import torch
from torch.utils.data import Dataset

from training.dataset_loader import (
    DatasetRecord,
    load_sample,
)


class SignBridgeDataset(Dataset):
    """
    Lazy-loading dataset.

    x:
        FloatTensor [64, 54, 2]

    y:
        LongTensor scalar class_id
    """

    def __init__(
        self,
        records: list[DatasetRecord],
    ) -> None:
        self.records = list(records)

    def __len__(self) -> int:
        return len(self.records)

    def __getitem__(
        self,
        index: int,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        record = self.records[index]

        sample = load_sample(record)

        x = torch.tensor(
            sample.model_input,
            dtype=torch.float32,
        )

        y = torch.tensor(
            record.class_id,
            dtype=torch.long,
        )

        if tuple(x.shape) != (64, 54, 2):
            raise RuntimeError(
                f"{record.sample_id}: "
                f"expected (64, 54, 2), got {tuple(x.shape)}"
            )

        return x, y
