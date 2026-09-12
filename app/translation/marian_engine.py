"""Local Hugging Face MarianMT implementation."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Literal

from .engine import TranslationEngine

LOGGER = logging.getLogger(__name__)
TranslationDevice = Literal["auto", "cpu", "cuda"]


class MarianTranslationEngine(TranslationEngine):
    def __init__(
        self,
        model_name: str = "Helsinki-NLP/opus-mt-en-ru",
        *,
        source_language: str = "en",
        target_language: str = "ru",
        device: TranslationDevice = "auto",
        cache_dir: Path = Path("models/translation"),
        offline: bool = False,
    ) -> None:
        import torch
        from transformers import MarianMTModel, MarianTokenizer

        cache_dir.mkdir(parents=True, exist_ok=True)
        self.supported_pair = (source_language, target_language)
        selected = "cuda" if device == "auto" and torch.cuda.is_available() else device
        if selected == "auto":
            selected = "cpu"
        if selected == "cuda" and not torch.cuda.is_available():
            LOGGER.warning("Translation CUDA requested but unavailable; using CPU")
            selected = "cpu"
        self.device = selected
        self._torch = torch
        LOGGER.info("Loading Marian model %s on %s", model_name, selected)
        self._tokenizer = MarianTokenizer.from_pretrained(
            model_name,
            cache_dir=cache_dir,
            local_files_only=offline,
        )
        self._model = MarianMTModel.from_pretrained(
            model_name,
            cache_dir=cache_dir,
            local_files_only=offline,
        )
        self._model.to(selected)
        self._model.eval()
        LOGGER.info("Marian translator is ready on %s", selected)

    def translate(
        self, text: str, source_language: str, target_language: str
    ) -> str:
        if (source_language, target_language) != self.supported_pair:
            raise ValueError(
                f"This Marian model supports only {self.supported_pair[0]}→"
                f"{self.supported_pair[1]}, got {source_language}→{target_language}."
            )
        normalized = text.strip()
        if not normalized:
            return ""
        tokens = self._tokenizer(
            normalized,
            return_tensors="pt",
            truncation=True,
            max_length=512,
        )
        tokens = {key: value.to(self.device) for key, value in tokens.items()}
        with self._torch.inference_mode():
            generated = self._model.generate(
                **tokens,
                max_new_tokens=256,
                num_beams=1,
            )
        return self._tokenizer.batch_decode(generated, skip_special_tokens=True)[0].strip()

    def close(self) -> None:
        model, self._model = self._model, None
        tokenizer, self._tokenizer = self._tokenizer, None
        del model, tokenizer
        if self.device == "cuda":
            self._torch.cuda.empty_cache()
