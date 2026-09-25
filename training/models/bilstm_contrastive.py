from __future__ import annotations

import torch
from torch import nn
from torch.nn import functional as F


class BiLSTMContrastiveBaseline(nn.Module):
    """
    SignBridge BiLSTM baseline with a training-only
    projection head for cross-signer contrastive learning.

    Input:
        [B, 64, 54, 2]

    Classification path stays close to the original baseline.
    """

    def __init__(
        self,
        num_classes: int,
        hidden_size: int = 128,
        projection_size: int = 128,
        num_layers: int = 1,
        dropout: float = 0.25,
    ) -> None:
        super().__init__()

        self.input_size = 54 * 2
        self.hidden_size = hidden_size

        self.lstm = nn.LSTM(
            input_size=self.input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
            bidirectional=True,
            dropout=(
                dropout
                if num_layers > 1
                else 0.0
            ),
        )

        feature_size = hidden_size * 2

        self.norm = nn.LayerNorm(
            feature_size
        )

        self.dropout = nn.Dropout(
            dropout
        )

        self.classifier = nn.Linear(
            feature_size,
            num_classes,
        )

        self.projection_head = nn.Sequential(
            nn.Linear(
                feature_size,
                feature_size,
            ),
            nn.ReLU(),
            nn.Linear(
                feature_size,
                projection_size,
            ),
        )


    def encode(
        self,
        x: torch.Tensor,
    ) -> torch.Tensor:

        if x.ndim != 4:
            raise ValueError(
                "Expected [B,64,54,2], "
                f"got {tuple(x.shape)}"
            )

        if tuple(
            x.shape[1:]
        ) != (
            64,
            54,
            2,
        ):
            raise ValueError(
                "Expected [B,64,54,2], "
                f"got {tuple(x.shape)}"
            )

        batch_size = x.shape[0]

        x = x.reshape(
            batch_size,
            64,
            self.input_size,
        )

        sequence, _ = self.lstm(
            x
        )

        pooled = sequence.mean(
            dim=1
        )

        return self.norm(
            pooled
        )


    def forward(
        self,
        x: torch.Tensor,
        return_projection: bool = False,
    ):

        features = self.encode(
            x
        )

        logits = self.classifier(
            self.dropout(
                features
            )
        )

        if not return_projection:
            return logits

        projection = (
            self.projection_head(
                features
            )
        )

        projection = F.normalize(
            projection,
            p=2,
            dim=1,
        )

        return (
            logits,
            projection,
        )
