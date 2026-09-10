from sqlalchemy import select
from sqlalchemy.orm import Session

from src.domain.models import ExerciseTemplateMedia


class ExerciseTemplateMediaRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_template_id(self, template_id: str) -> ExerciseTemplateMedia | None:
        return self.db.scalar(select(ExerciseTemplateMedia).where(ExerciseTemplateMedia.template_id == template_id))

    def get_media_for_template_ids(self, template_ids: list[str]) -> list[ExerciseTemplateMedia]:
        if not template_ids:
            return []
        return list(
            self.db.scalars(
                select(ExerciseTemplateMedia).where(ExerciseTemplateMedia.template_id.in_(template_ids))
            ).all()
        )

    def upsert_verified_media(
        self,
        *,
        template_id: str,
        source: str,
        image_url: str | None,
        local_file_name: str | None,
        alt_text: str,
        attribution: str | None = None,
        is_verified: bool = False,
    ) -> ExerciseTemplateMedia:
        media = self.get_by_template_id(template_id)
        if media is None:
            media = ExerciseTemplateMedia(
                template_id=template_id,
                source=source,
                image_url=image_url,
                local_file_name=local_file_name,
                alt_text=alt_text,
                attribution=attribution,
                is_verified=is_verified,
            )
            self.db.add(media)
        else:
            media.source = source
            media.image_url = image_url
            media.local_file_name = local_file_name
            media.alt_text = alt_text
            media.attribution = attribution
            media.is_verified = is_verified
        self.db.commit()
        self.db.refresh(media)
        return media

    def delete_local_media(self, template_id: str) -> None:
        media = self.get_by_template_id(template_id)
        if media is not None:
            self.db.delete(media)
            self.db.commit()
