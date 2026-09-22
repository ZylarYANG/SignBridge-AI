from __future__ import annotations

import torch
from torch import nn


class BiLSTMBaseline(nn.Module):
    """
    SignBridge minimal temporal baseline.

    Input:
        [B, 64, 54, 2]

    Output:
        [B, num_classes]
    """

    def __init__(
        self,
        num_classes: int,
        hidden_size: int = 128,
        num_layers: int = 1,
        dropout: float = 0.25,
    ) -> None:
        super().__init__()

        self.input_size = 54 * 2

        self.lstm = nn.LSTM(
            input_size=self.input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
            bidirectional=True,
            dropout=dropout if num_layers > 1 else 0.0,
        )

        self.norm = nn.LayerNorm(hidden_size * 2)
        self.dropout = nn.Dropout(dropout)

        self.classifier = nn.Linear(
            hidden_size * 2,
            num_classes,
        )

    def forward(
        self,
        x: torch.Tensor,
    ) -> torch.Tensor:
        if x.ndim != 4:
            raise ValueError(
                f"Expected [B, 64, 54, 2], got {tuple(x.shape)}"
            )

        if tuple(x.shape[1:]) != (64, 54, 2):
            raise ValueError(
                f"Expected [B, 64, 54, 2], got {tuple(x.shape)}"
            )

        batch_size = x.shape[0]

        x = x.reshape(
            batch_size,
            64,
            self.input_size,
        )

        sequence_output, _ = self.lstm(x)

        pooled = sequence_output.mean(dim=1)
        pooled = self.norm(pooled)
        pooled = self.dropout(pooled)

        return self.classifier(pooled)
