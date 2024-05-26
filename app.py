import logging

from sqlalchemy.orm import Session
from sqlalchemy import select

import db
import models
import menu
import exceptions
import sample_services

LOGGER = logging.getLogger('sample_organiser')
MENU_LOGGER = logging.getLogger('sample_organiser/menu')
logging.basicConfig(level=logging.INFO)


class TagMenu(menu.ObjectMenu):
    MAPPING = {
        "af": "add_filter",
        "rf": "remove_filter",
        "s": "samples",
    }

    def menu_info(self):
        MENU_LOGGER.info(f"Tag: {self.object.name}")
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


class TagsMenu(menu.PagedMenu):
    MODEL = models.Tag

    def number_options(self):
        MENU_LOGGER.info("#. Select tag")

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


class SampleMenu(menu.ObjectMenu):
    MAPPING = {
        "p": "play_sample",
        "r": "set_rating",
        "a": "add_tag",
        "rt": "remove_tag",
    }

    def __init__(self, session, obj, object_index, parent):
        super().__init__(session, obj, object_index, parent)

    def menu_info(self):
        self.play_sample()
        MENU_LOGGER.info(f"Sample: {self.object.filename}")
        MENU_LOGGER.info(f"Rating: {self.object.rating}")
        MENU_LOGGER.info(f"Tags: {', '.join([x.name for x in self.object.tags])}")

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

    def play_sample(self):
        sample_services.play_sample(self.object)

    def set_rating(self):
        rating = input("Enter the rating: ")
        self.object.rating = int(rating)
        self.session.commit()


class SamplesMenu(menu.PagedMenu):
    MODEL = models.Sample

    def number_options(self):
        MENU_LOGGER.info("#. Select sample")

    def number_option_handler(self, choice):
        if choice.isdigit():
            sample_index = int(choice) - 1
            sample = self.page_of_objects[sample_index]
            if sample:
                SampleMenu(self.session, sample, sample_index, self).run()
            else:
                MENU_LOGGER.info("Sample not found")
        else:
            MENU_LOGGER.info("Unknown option")


class MainMenu(menu.Menu):
    MAPPING = {
        "1": "add_directory",
        "2": "list_tags",
        "3": "list_samples",
        "4": "list_samples_for_tag",
        "5": "load_defaults"
    }

    def menu_info(self):
        total_samples_count = self.session.query(models.Sample).count()
        MENU_LOGGER.info(f"Total samples: {total_samples_count}")

    def add_directory(self):
        path = input("Enter the path to the directory: ")
        sample_services.find_samples_in_dir(self.session, path)
        self.session.commit()

    def list_tags(self):
        TagsMenu(self.session).run()

    def list_samples(self):
        SamplesMenu(self.session).run()

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


def main():
    with Session(db.engine) as session:
        menu = MainMenu(session)
        menu.run()


if __name__ == __name__:
    db.Base.metadata.create_all(db.engine)
    main()
