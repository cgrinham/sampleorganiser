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
    collections: Mapped[List["Sample"]] = relationship("Collection", secondary="collection_tag_associations", back_populates="tags")

    def __repr__(self) -> str:
        return f"Tag {self.id}: {self.name}"

    @classmethod
    def get_by_name(cls, session, name: str):
        return session.scalars(select(Tag).where(Tag.name == name)).one_or_none()

    @classmethod
    def load_defaults(cls, session):
        LOGGER.info("Load defaults")
        with open('defaults.toml', 'rb') as f:
            data = tomllib.load(f)
            for tag in data['default_tags']:
                session.add(cls(
                    name=tag["name"],
                    filters=[TagFilter(string=x) for x in tag.get("filters", [])]
                ))
            session.commit()
        LOGGER.info("Defaults loaded")

    def add_filter(self, session, filter_string: str):
        self.filters.append(TagFilter(string=filter_string))
        session.commit()

    def remove_filter(self, session, filter_string: str):
        self.filters = [x for x in self.filters if x.string != filter_string]
        session.commit()


class TaggedModel:
    def add_tag(self, session, tag_or_name, create: bool = False):
        if not isinstance(tag_or_name, Tag):
            tag = Tag.get_by_name(session, tag_or_name)
        if tag:
            self.tags.append(tag)
        else:
            if not create:
                raise exceptions.NotFoundError()
            tag = Tag(name=tag_or_name)
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


class Sample(db.Base, TaggedModel):

    __tablename__ = "samples"

    name: Mapped[Optional[str]] = mapped_column(String(256))
    path: Mapped[str] = mapped_column(String(1024), unique=True)
    tags: Mapped[List[Tag]] = relationship("Tag", secondary="sample_tag_associations", back_populates="samples")
    collections: Mapped[List[Tag]] = relationship("Collection", secondary="collection_sample_associations", back_populates="samples")
    rating: Mapped[Optional[int]] = mapped_column(Integer)

    def __repr__(self) -> str:
        return f"Sample {self.id}: Rating={self.rating} Filename={self.filename}"

    @property
    def filename(self) -> str:
        return self.path.split("/")[-1]


class SampleTagAssociation(db.Base):

    __tablename__ = "sample_tag_associations"

    sample_id: Mapped[int] = mapped_column(ForeignKey("samples.id"))
    tag_id: Mapped[int] = mapped_column(ForeignKey("tags.id"))
    uq = UniqueConstraint("sample_id", "tag_id")


class Collection(db.Base, TaggedModel):

    __tablename__ = "collections"

    name: Mapped[str] = mapped_column(String(256), nullable=False)
    samples: Mapped[List["Sample"]] = relationship("Sample", secondary="collection_sample_associations", back_populates="collections")
    tags: Mapped[List[Tag]] = relationship("Tag", secondary="collection_tag_associations", back_populates="collections")

    def __repr__(self) -> str:
        return f"Collection {self.id}: {self.name}"

    def add_sample(self, session, sample: Sample):
        self.samples.append(sample)
        session.commit()

    def remove_sample(self, session, sample: Sample):
        self.samples.remove(sample)
        session.commit()


class CollectionTagAssociation(db.Base):

    __tablename__ = "collection_tag_associations"

    collection_id: Mapped[int] = mapped_column(ForeignKey("collections.id"))
    tag_id: Mapped[int] = mapped_column(ForeignKey("tags.id"))
    uq = UniqueConstraint("collection_id", "tag_id")


class CollectionSampleAssociation(db.Base):

    __tablename__ = "collection_sample_associations"

    collection_id: Mapped[int] = mapped_column(ForeignKey("collections.id"))
    sample_id: Mapped[int] = mapped_column(ForeignKey("samples.id"))
    uq = UniqueConstraint("collection_id", "sample_id")
