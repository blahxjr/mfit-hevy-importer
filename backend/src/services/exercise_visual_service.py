from __future__ import annotations

from typing import Any

from src.domain.models import ExerciseTemplate, ExerciseTemplateMedia


class ExerciseVisualService:
    @staticmethod
    def get_visual_descriptor(template: ExerciseTemplate | None, media: ExerciseTemplateMedia | None) -> dict[str, Any]:
        source = "placeholder"
        image_url = None
        local_image_url = None
        alt_text = "Imagem de referência para exercício"
        movement_icon = ExerciseVisualService._movement_icon(template)
        muscle_label = template.primary_muscle_group if template and template.primary_muscle_group else None
        equipment_label = template.equipment if template and template.equipment else None

        if media is not None:
            if media.source == "placeholder":
                source = "placeholder"
            elif media.source == "hevy_official" and media.image_url:
                source = "official_image"
                image_url = media.image_url
                alt_text = media.alt_text or alt_text
            elif media.source == "local_manual":
                source = "local_image"
                local_image_url = media.image_url or None
                image_url = media.image_url or None
                alt_text = media.alt_text or alt_text

        if template is not None and not alt_text:
            alt_text = f"Imagem de referência para {template.title}"
        if template is not None and source == "placeholder":
            alt_text = media.alt_text if media and media.alt_text else f"Imagem de referência para {template.title}"

        if template is not None and template.title and source == "placeholder":
            movement_icon = ExerciseVisualService._movement_icon(template)
            muscle_label = template.primary_muscle_group or None
            equipment_label = template.equipment or None

        return {
            "template_id": template.id if template else None,
            "kind": source,
            "image_url": image_url,
            "local_image_url": local_image_url,
            "alt_text": alt_text,
            "movement_icon": movement_icon,
            "muscle_label": muscle_label,
            "equipment_label": equipment_label,
            "is_verified": bool(media.is_verified) if media else False,
        }

    @staticmethod
    def _movement_icon(template: ExerciseTemplate | None) -> str:
        if template is None:
            return "bi-card-image"
        title = (template.title or "").lower()
        if any(token in title for token in ["pull", "row", "lat", "rear delt", "back"]):
            return "bi-arrow-up-right"
        if any(token in title for token in ["press", "bench", "push", "dip", "overhead"]):
            return "bi-arrow-up"
        if any(token in title for token in ["squat", "lunge", "deadlift", "hinge"]):
            return "bi-arrows-collapse"
        if any(token in title for token in ["curl", "arm", "biceps", "tricep"]):
            return "bi-circle"
        return "bi-card-image"

    @staticmethod
    def build_placeholder(template: ExerciseTemplate | None, title_hint: str | None = None) -> dict[str, Any]:
        title = (template.title if template else None) or title_hint or "Exercício"
        return {
            "template_id": template.id if template else None,
            "kind": "placeholder",
            "image_url": None,
            "local_image_url": None,
            "alt_text": f"Imagem de referência para {title}",
            "movement_icon": ExerciseVisualService._movement_icon(template),
            "muscle_label": template.primary_muscle_group if template and template.primary_muscle_group else None,
            "equipment_label": template.equipment if template and template.equipment else None,
            "is_verified": False,
        }
