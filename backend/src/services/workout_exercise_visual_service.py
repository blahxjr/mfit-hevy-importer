from typing import Any

from src.services.exercise_visual_service import ExerciseVisualService


class WorkoutExerciseVisualService:
    @staticmethod
    def get_visual_descriptor_for_workout_exercise(
        import_id: str, exercise_index: int, template: Any, media: Any, generic_media: dict[str, Any] | None
    ) -> dict[str, Any]:
        if media is not None and media.source == "local_manual":
            descriptor = ExerciseVisualService.get_visual_descriptor(template, media)
            descriptor.update({"import_id": import_id, "exercise_index": exercise_index, "source": "local_manual"})
            return descriptor
        if generic_media:
            descriptor = ExerciseVisualService.build_placeholder(template)
            descriptor.update(
                {
                    "import_id": import_id,
                    "exercise_index": exercise_index,
                    "kind": "generic_image",
                    "source": "generic_library",
                    "image_url": generic_media["image_url"],
                    "local_image_url": generic_media["image_url"],
                    "alt_text": generic_media["alt_text"],
                    "is_verified": False,
                }
            )
            return descriptor
        descriptor = ExerciseVisualService.build_placeholder(template)
        descriptor.update({"import_id": import_id, "exercise_index": exercise_index, "source": "none"})
        return descriptor
