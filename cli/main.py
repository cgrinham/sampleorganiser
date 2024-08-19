import logging

from sqlalchemy import select

import models
import exceptions
import sample_services
import audio
from . import classes as menu_classes

LOGGER = logging.getLogger('sample_organiser')
MENU_LOGGER = logging.getLogger('sample_organiser/menu')


class TagMenu(menu_classes.ObjectMenu):
    MAPPING = {
        "af": "add_filter",
        "rf": "remove_filter",
        "s": "samples",
    }

    def menu_info(self):
        MENU_LOGGER.info(f"== Tag: {self.object.name}")
        MENU_LOGGER.info(f"Filters: {', '.join([x.string for x in self.object.filters])}")
        MENU_LOGGER.info(f"Samples: {len(self.object.samples)}")

    def samples(self):
        samples_query = select(models.Sample).join(models.Sample.tags).where(models.Tag.name == self.object.name)
        SamplesMenu(self.session, samples_query).run()

    def add_filter(self):
        filter_string = input("Enter the filter string: ")
        self.object.add_filter(self.session, filter_string)

    def remove_filter(self):
        filter_string = input("Enter the filter string: ")
        self.object.remove_filter(self.session, filter_string)


class TagsMenu(menu_classes.PagedMenu):
    MODEL = models.Tag

    def menu_info(self):
        MENU_LOGGER.info("== Tags")
        for index, obj in enumerate(self.page_of_objects):
            MENU_LOGGER.info(f"{index + 1} - {obj.name}: {len(obj.samples)} samples")

    def number_options(self):
        MENU_LOGGER.info("  #. Select tag")

    def number_option_handler(self, choice):
        if choice.isdigit():
            tag_index = int(choice) - 1
            tag = self.page_of_objects[tag_index]
            if tag:
                TagMenu(self.session, tag, tag_index, self).run()
            else:
                MENU_LOGGER.info("Tag not found")
        else:
            MENU_LOGGER.info("Unknown option")


class TaggedObjectMenuMixin:

    def __init__(self, session, obj, object_index, parent):
        self.MAPPING.update({
            "a": "add_tag",
            "rt": "remove_tag",
        })
        super().__init__(session, obj, object_index, parent)

    def add_tag(self):
        tag_name = input("Enter the tag name: ")
        try:
            self.object.add_tag(self.session, tag_name)
            self.session.commit()
        except exceptions.NotFoundError:
            MENU_LOGGER.info("Tag not found, create it?")
            choice = input("y/n: ")
            if choice == "y":
                self.object.add_tag(self.session, tag_name, create=True)

    def remove_tag(self):
        tag_name = input("Enter the tag name: ")
        self.object.remove_tag(self.session, tag_name)


class SampleMenu(TaggedObjectMenuMixin, menu_classes.ObjectMenu):
    MAPPING = {
        "ps": "play_sample",
        "psj": "play_sample_with_jack",
        "r": "set_rating",
        "ac": "add_to_collection",
        "rc": "remove_from_collection",
    }

    def __init__(self, session, obj, object_index, parent):
        super().__init__(session, obj, object_index, parent)

    def menu_info(self):
        MENU_LOGGER.info("")
        MENU_LOGGER.info(f"== Sample: {self.object.filename}")
        MENU_LOGGER.info(f"Rating: {self.object.rating}")
        MENU_LOGGER.info(f"Tags: {', '.join([x.name for x in self.object.tags])}")
        self.play_sample(wait=False)

    def play_sample(self, wait=True):
        sample_services.play_sample(self.object, wait=wait)

    def play_sample_with_jack(self):
        audio.play_sample(self.object)

    def set_rating(self):
        rating = input("Enter the rating: ")
        self.object.rating = int(rating)
        self.session.commit()

    def add_to_collection(self):
        collection_name = input("Enter the collection name: ")
        collection = self.session.query(models.Collection).filter(models.Collection.name == collection_name).first()
        if not collection:
            MENU_LOGGER.info("Collection not found")
            return
        if self.object not in collection.samples:
            collection.add_sample(self.session, self.object)


class CollectionMenu(menu_classes.ObjectMenu, TaggedObjectMenuMixin):
    MAPPING = {
        "rs": "remove_sample",
    }

    def menu_info(self):
        MENU_LOGGER.info("")
        MENU_LOGGER.info(f"== Collection: {self.object.name}")
        MENU_LOGGER.info("Samples:")
        for sample in self.object.samples:
            MENU_LOGGER.info(f"  - {sample.filename}")

    def remove_sample(self):
        sample_path = input("Enter the sample path: ")
        sample = self.session.query(models.Sample).filter(models.Sample.path == sample_path).first()
        if not sample:
            MENU_LOGGER.info("Sample not found")
            return
        self.object.samples.remove(sample)
        self.session.commit()


class SamplesMenu(menu_classes.PagedMenu):
    MODEL = models.Sample
    MODEL_MENU = SampleMenu
    SORT_OPTIONS = [("Name", "asc"), ("Rating", "desc")]


class CollectionsMenu(menu_classes.PagedMenu):
    MODEL = models.Collection
    MODEL_MENU = CollectionMenu
    SORT_OPTIONS = [("Name", "asc")]

    MAPPING = {
        "nc": "new_collection",
    }

    def new_collection(self):
        collection_name = input("Enter the collection name: ")
        collection = models.Collection(name=collection_name)
        self.session.add(collection)
        self.session.commit()
        MENU_LOGGER.info(f"Collection {collection_name} created")
        self.load_page()


class MainMenu(menu_classes.Menu):
    MAPPING = [
        "add_directory",
        "samples",
        "collections",
        "tags",
        "list_samples_for_tag",
        "load_defaults",
    ]

    def menu_info(self):
        total_samples_count = self.session.query(models.Sample).count()
        MENU_LOGGER.info(f"Total samples: {total_samples_count}")

    def add_directory(self):
        path = input("Enter the path to the directory: ")
        sample_services.find_samples_in_dir(self.session, path)
        self.session.commit()

    def tags(self):
        TagsMenu(self.session).run()

    def samples(self):
        SamplesMenu(self.session).run()

    def collections(self):
        CollectionsMenu(self.session).run()

    def list_samples_for_tag(self):
        tag_name = input("Enter the tag name: ")
        tag = self.session.execute(select(models.Tag).where(models.Tag.name == tag_name)).first()
        if not tag:
            MENU_LOGGER.info("Tag not found")
            return
        samples_query = select(models.Sample).join(models.Sample.tags).where(models.Tag.name == tag_name)
        SamplesMenu(self.session, samples_query).run()

    def load_defaults(self):
        models.Tag.load_defaults(self.session)
        MENU_LOGGER.info("Defaults loaded")
