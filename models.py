import tomllib
import logging

from typing import List
from typing import Optional
from sqlalchemy import ForeignKey
from sqlalchemy import String, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship
from sqlalchemy import select

import db
import exceptions


LOGGER = logging.getLogger('sample_organiser')


class TagFilter(db.Base):
    __tablename__ = "tag_filters"

    string: Mapped[str] = mapped_column(String(32), nullable=False)
    tag_id: Mapped[int] = mapped_column(ForeignKey("tags.id"))


class Tag(db.Base):

    __tablename__ = "tags"

    name: Mapped[str] = mapped_column(String(256), nullable=False, unique=True)
    filters: Mapped[List[TagFilter]] = relationship("TagFilter")
    samples: Mapped[List["Sample"]] = relationship("Sample", secondary="sample_tag_associations", back_populates="tags")

    def __repr__(self) -> str:
        return f"Tag {self.id}: {self.name}"

    def get_by_name(self, session, name):
        return self.session.execute(select(Tag).where(Tag.name == name)).one_or_none()

    def load_defaults(self, session):
        LOGGER.info("Load defaults")
        with open('defaults.toml', 'rb') as f:
            data = tomllib.load(f)
            for tag in data['default_tags']:
                session.add(Tag(
                    name=tag["name"],
                    filters=[TagFilter(string=x) for x in tag["filters"]]
                ))
            session.commit()
        LOGGER.info("Defaults loaded")

    def add_filter(self, session, filter_string):
        self.filters.append(TagFilter(string=filter_string))
        session.commit()

    def remove_filter(self, session, filter_string):
        self.filters = [x for x in self.filters if x.string != filter_string]
        session.commit()


class Sample(db.Base):

    __tablename__ = "samples"

    name: Mapped[Optional[str]] = mapped_column(String(256))
    path: Mapped[str] = mapped_column(String(1024), unique=True)
    tags: Mapped[List[Tag]] = relationship("Tag", secondary="sample_tag_associations", back_populates="samples")
    rating: Mapped[Optional[int]] = mapped_column(Integer)

    def __repr__(self) -> str:
        return f"Sample {self.id}: Rating={self.rating} Filename={self.filename}"

    @property
    def filename(self):
        return self.path.split("/")[-1]

    def add_tag(self, session, tag_name, create=False):
        tag = Tag.get_by_name(session, tag_name)
        if tag:
            self.sample.tags.remove(tag)
        else:
            if not create:
                raise exceptions.NotFoundError()
            tag = Tag(name=tag_name)
            session.add(tag)
            session.flush()
            self.tags.append(tag)
            session.flush()

    def remove_tag(self, session, tag_name):
        tag = [x for x in self.tags if x.name == tag_name]
        if not tag:
            return
        self.tags.remove(tag)
        session.commit()


class SampleTagAssociation(db.Base):

    __tablename__ = "sample_tag_associations"

    sample_id: Mapped[int] = mapped_column(ForeignKey("samples.id"))
    tag_id: Mapped[int] = mapped_column(ForeignKey("tags.id"))
    uq = UniqueConstraint("sample_id", "tag_id")
