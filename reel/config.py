"""Brand configuration. Visual and audio grammar intentionally stays locked."""
from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "reel.config.json"
DEFAULT_ACCENT = "#fb7185"


@dataclass(frozen=True)
class BrandConfig:
    handle: str = "@buildebugship"
    accent: str = DEFAULT_ACCENT
    cta: str = "Follow @buildebugship for backend architecture explained visually."
    caption_attribution: str = "@buildebugship"

    def validate(self) -> "BrandConfig":
        if not re.fullmatch(r"@[A-Za-z0-9_.]{1,30}", self.handle):
            raise ValueError("brand handle must start with @ and contain only letters, digits, _ or .")
        if not re.fullmatch(r"#[0-9a-fA-F]{6}", self.accent):
            raise ValueError("brand accent must be a six-digit hex color")
        if not self.cta.strip() or not self.caption_attribution.strip():
            raise ValueError("CTA and caption attribution cannot be empty")
        return self


def load_brand(path: Path = CONFIG_PATH) -> BrandConfig:
    data = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    allowed = set(asdict(BrandConfig()))
    unknown = sorted(set(data) - allowed)
    if unknown:
        raise ValueError(f"unknown brand config fields: {', '.join(unknown)}")
    return BrandConfig(**data).validate()
