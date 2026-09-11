import json
import re
from pathlib import Path
from typing import Any


LIBRARY_ROOT = Path(__file__).resolve().parents[2] / "data" / "generic-movement-library"
MAPPING_PATH = LIBRARY_ROOT / "mapping.json"
MOVEMENTS = {"push_horizontal", "push_vertical", "pull_vertical", "pull_horizontal", "squat", "hinge", "carry", "core"}


def _mapping() -> dict[str, Any]:
    if not MAPPING_PATH.exists():
        return {"movements": {}, "template_to_movement": {}}
    return json.loads(MAPPING_PATH.read_text(encoding="utf-8"))


class GenericMovementLibraryService:
    @staticmethod
    def get_movement_for_template(template: Any) -> str | None:
        if template is None:
            return None
        data = _mapping()
        title = (getattr(template, "title", "") or "").lower()
        normalized = re.sub(r"[^a-z0-9]+", "_", title).strip("_")
        direct = data.get("template_to_movement", {})
        if normalized in direct and direct[normalized] in MOVEMENTS:
            return direct[normalized]
        primary = (getattr(template, "primary_muscle_group", "") or "").lower()
        equipment = (getattr(template, "equipment", "") or "").lower()
        text = f"{title} {primary} {equipment}"
        rules = (
            ("push_horizontal", ("bench", "chest press", "push up", "push-up", "chest")),
            ("push_vertical", ("overhead", "shoulder press", "military press")),
            ("pull_vertical", ("pulldown", "pull down", "pull-up", "pullup", "lat")),
            ("pull_horizontal", ("row", "remada", "back")),
            ("squat", ("squat", "agachamento", "lunge", "leg press", "quadriceps")),
            ("hinge", ("deadlift", "dead lift", "romanian", "stiff", "hinge", "hamstring")),
            ("carry", ("farmer", "carry", "walk")),
            ("core", ("plank", "crunch", "abdominal", "abs", "core")),
        )
        for movement, keywords in rules:
            if any(keyword in text for keyword in keywords):
                return movement
        return None

    @staticmethod
    def get_generic_media_for_movement(movement: str) -> dict[str, Any] | None:
        if movement not in MOVEMENTS:
            return None
        entry = _mapping().get("movements", {}).get(movement)
        if not entry:
            return None
        file_name = str(entry.get("file_name", ""))
        if not file_name or Path(file_name).name != file_name:
            return None
        path = LIBRARY_ROOT / file_name
        if not path.is_file():
            return None
        return {
            "source": "generic_library",
            "local_file_name": file_name,
            "image_url": f"/static/generic-movement-library/{file_name}",
            "alt_text": entry.get("alt_text") or "Imagem genérica do padrão de movimento",
            "is_verified": False,
        }

    @classmethod
    def get_generic_media_for_template(cls, template: Any) -> dict[str, Any] | None:
        movement = cls.get_movement_for_template(template)
        return cls.get_generic_media_for_movement(movement) if movement else None
