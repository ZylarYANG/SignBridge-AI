from __future__ import annotations

import torch
from torch import nn


class BiLSTMHandshapeAttention(nn.Module):
    """
    SignBridge handshape-aware temporal model.

    Input:
        [B, 64, 54, 2]

    Per-frame features:
        body-normalized canonical coordinates
        +
        wrist-relative, palm-normalized handshape

    Temporal aggregation:
        BiLSTM
        +
        learned temporal attention
        +
        mean pooling
    """

    def __init__(
        self,
        num_classes: int,
        hidden_size: int = 128,
        num_layers: int = 1,
        dropout: float = 0.25,
    ) -> None:
        super().__init__()

        self.num_landmarks = 54
        self.base_feature_size = 54 * 2

        # 21 left + 21 right, each x/y.
        self.handshape_feature_size = (
            42 * 2
        )

        self.input_size = (
            self.base_feature_size
            + self.handshape_feature_size
        )

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

        temporal_size = (
            hidden_size * 2
        )

        self.sequence_norm = nn.LayerNorm(
            temporal_size
        )

        self.attention = nn.Sequential(
            nn.Linear(
                temporal_size,
                hidden_size,
            ),
            nn.Tanh(),
            nn.Linear(
                hidden_size,
                1,
            ),
        )

        # attention pooled + mean pooled
        self.classifier = nn.Sequential(
            nn.Linear(
                temporal_size * 2,
                temporal_size,
            ),
            nn.ReLU(),
            nn.Dropout(
                dropout
            ),
            nn.Linear(
                temporal_size,
                num_classes,
            ),
        )


    @staticmethod
    def _point_valid(
        hand: torch.Tensor,
    ) -> torch.Tensor:
        """
        model_input uses [0,0] for missing points.

        This is only used for the handshape branch.
        """
        return (
            hand.abs()
            .sum(
                dim=-1,
                keepdim=True,
            )
            > 1e-8
        )


    @classmethod
    def _normalize_hand(
        cls,
        hand: torch.Tensor,
    ) -> torch.Tensor:
        """
        hand:
            [B,T,21,2]

        Normalize hand geometry relative to wrist,
        using MCP landmarks as palm-scale reference.
        """

        wrist = hand[
            :,
            :,
            0:1,
            :
        ]

        valid = cls._point_valid(
            hand
        )

        wrist_valid = valid[
            :,
            :,
            0:1,
            :
        ]

        # MediaPipe hand MCP landmarks:
        # index 5, middle 9, ring 13, little 17.
        anchors = hand[
            :,
            :,
            [5, 9, 13, 17],
            :
        ]

        anchor_valid = valid[
            :,
            :,
            [5, 9, 13, 17],
            :
        ]

        anchor_valid = (
            anchor_valid
            & wrist_valid
        )

        distances = torch.linalg.vector_norm(
            anchors - wrist,
            dim=-1,
            keepdim=True,
        )

        mask = anchor_valid.to(
            hand.dtype
        )

        scale = (
            (
                distances
                * mask
            ).sum(
                dim=2,
                keepdim=True,
            )
            /
            mask.sum(
                dim=2,
                keepdim=True,
            ).clamp_min(
                1.0
            )
        )

        scale = scale.clamp_min(
            1e-3
        )

        normalized = (
            hand - wrist
        ) / scale

        usable = (
            valid
            & wrist_valid
        )

        normalized = torch.where(
            usable,
            normalized,
            torch.zeros_like(
                normalized
            ),
        )

        return normalized


    def forward(
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

        batch_size = (
            x.shape[0]
        )

        # ---------------------------------
        # Base canonical-position branch
        # ---------------------------------

        base_features = x.reshape(
            batch_size,
            64,
            self.base_feature_size,
        )

        # ---------------------------------
        # Handshape branch
        # ---------------------------------

        left_hand = x[
            :,
            :,
            0:21,
            :
        ]

        right_hand = x[
            :,
            :,
            21:42,
            :
        ]

        left_shape = (
            self._normalize_hand(
                left_hand
            )
        )

        right_shape = (
            self._normalize_hand(
                right_hand
            )
        )

        handshape = torch.cat(
            (
                left_shape,
                right_shape,
            ),
            dim=2,
        )

        handshape = handshape.reshape(
            batch_size,
            64,
            self.handshape_feature_size,
        )

        # ---------------------------------
        # Joint representation
        # ---------------------------------

        features = torch.cat(
            (
                base_features,
                handshape,
            ),
            dim=-1,
        )

        sequence, _ = self.lstm(
            features
        )

        sequence = self.sequence_norm(
            sequence
        )

        # ---------------------------------
        # Learned temporal attention
        # ---------------------------------

        attention_logits = (
            self.attention(
                sequence
            )
            .squeeze(
                -1
            )
        )

        attention_weights = (
            torch.softmax(
                attention_logits,
                dim=1,
            )
        )

        attention_pooled = (
            sequence
            * attention_weights.unsqueeze(
                -1
            )
        ).sum(
            dim=1
        )

        # Preserve global context as well.
        mean_pooled = (
            sequence.mean(
                dim=1
            )
        )

        pooled = torch.cat(
            (
                attention_pooled,
                mean_pooled,
            ),
            dim=-1,
        )

        return self.classifier(
            pooled
        )
