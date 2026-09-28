from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Any

import numpy as np
import torch

from training.models.bilstm_baseline import BiLSTMBaseline


PROJECT_ROOT = Path(__file__).resolve().parents[3]

DEFAULT_CHECKPOINT = (
    PROJECT_ROOT
    / "training"
    / "experiments"
    / "formal_12class"
    / "bilstm_s004val_s005test.pt"
)


class RecognitionServiceError(RuntimeError):
    pass


class RecognitionService:
    def __init__(
        self,
        checkpoint_path: Path | None = None,
    ) -> None:
        self.checkpoint_path = (
            checkpoint_path
            or self._resolve_checkpoint_path()
        )

        self.device = self._resolve_device()

        if not self.checkpoint_path.exists():
            raise RecognitionServiceError(
                "Recognition checkpoint not found: "
                f"{self.checkpoint_path}"
            )

        try:
            checkpoint = torch.load(
                self.checkpoint_path,
                map_location=self.device,
                weights_only=False,
            )
        except Exception as exc:
            raise RecognitionServiceError(
                "Failed to load recognition checkpoint: "
                f"{self.checkpoint_path}"
            ) from exc

        try:
            self.num_classes = int(
                checkpoint["num_classes"]
            )
            self.hidden_size = int(
                checkpoint["hidden_size"]
            )

            self.class_mapping = {
                int(class_id): value
                for class_id, value
                in checkpoint["class_mapping"].items()
            }

            self.dataset_snapshot_sha256 = str(
                checkpoint.get(
                    "dataset_snapshot_sha256",
                    "",
                )
            )

            self.model = BiLSTMBaseline(
                num_classes=self.num_classes,
                hidden_size=self.hidden_size,
            ).to(self.device)

            self.model.load_state_dict(
                checkpoint["model_state_dict"]
            )

            self.model.eval()

        except Exception as exc:
            raise RecognitionServiceError(
                "Recognition checkpoint is incompatible "
                "with BiLSTMBaseline."
            ) from exc

        if len(self.class_mapping) != self.num_classes:
            raise RecognitionServiceError(
                "Checkpoint class_mapping size does not "
                "match num_classes."
            )

    @staticmethod
    def _resolve_device() -> torch.device:
        requested = os.getenv(
            "SIGNBRIDGE_DEVICE",
            "auto",
        ).strip().lower()

        if requested == "cpu":
            return torch.device("cpu")

        if requested == "cuda":
            if not torch.cuda.is_available():
                raise RecognitionServiceError(
                    "SIGNBRIDGE_DEVICE=cuda was requested "
                    "but CUDA is unavailable."
                )
            return torch.device("cuda")

        if requested != "auto":
            raise RecognitionServiceError(
                "SIGNBRIDGE_DEVICE must be one of: "
                "auto, cpu, cuda."
            )

        return torch.device(
            "cuda"
            if torch.cuda.is_available()
            else "cpu"
        )

    @staticmethod
    def _resolve_checkpoint_path() -> Path:
        configured = os.getenv(
            "SIGNBRIDGE_RECOGNITION_CHECKPOINT"
        )

        if not configured:
            return DEFAULT_CHECKPOINT

        path = Path(configured)

        if not path.is_absolute():
            path = PROJECT_ROOT / path

        return path.resolve()

    def _candidate(
        self,
        class_id: int,
        confidence: float,
    ) -> dict[str, Any]:
        info = self.class_mapping[class_id]

        return {
            "model_class_id": class_id,
            "original_class_id": int(
                info["original_class_id"]
            ),
            "sign_id": str(
                info["sign_id"]
            ),
            "label": str(
                info["label"]
            ),
            "confidence": float(confidence),
        }

    def predict(
        self,
        landmarks: list[list[list[float]]]
        | np.ndarray,
        top_k: int = 3,
    ) -> dict[str, Any]:
        array = np.asarray(
            landmarks,
            dtype=np.float32,
        )

        expected_shape = (64, 54, 2)

        if array.shape != expected_shape:
            raise RecognitionServiceError(
                "Expected recognition input shape "
                f"{expected_shape}, got {array.shape}."
            )

        if not np.isfinite(array).all():
            raise RecognitionServiceError(
                "Recognition input contains "
                "NaN or infinity."
            )

        tensor = (
            torch.from_numpy(array)
            .unsqueeze(0)
            .to(self.device)
        )

        with torch.inference_mode():
            logits = self.model(tensor)
            probabilities = torch.softmax(
                logits,
                dim=1,
            )[0]

            k = min(
                int(top_k),
                self.num_classes,
            )

            values, indices = torch.topk(
                probabilities,
                k=k,
            )

        candidates = [
            self._candidate(
                int(class_id),
                float(confidence),
            )
            for confidence, class_id
            in zip(
                values.detach().cpu().tolist(),
                indices.detach().cpu().tolist(),
            )
        ]

        return {
            "prediction": candidates[0],
            "top3": candidates,
            "checkpoint_name":
                self.checkpoint_path.name,
            "device": str(self.device),
            "dataset_snapshot_sha256":
                self.dataset_snapshot_sha256,
        }


@lru_cache(maxsize=1)
def get_recognition_service() -> RecognitionService:
    return RecognitionService()
