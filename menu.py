import logging

from sqlalchemy import select

MENU_LOGGER = logging.getLogger('sample_organiser/menu')
LOGGER = logging.getLogger('sample_organiser')


class Menu:
    MAPPING = {}

    def __init__(self, session, parent=None):
        self.session = session
        self.parent = parent

    def run(self):
        while True:
            self.menu_info()
            for key, method in self.MAPPING.items():
                MENU_LOGGER.info(f"{key}. {method.replace('_', ' ').title()}")
            self.number_options()
            MENU_LOGGER.info("q. Quit")
            choice = input("Enter a choice: ")
            if choice in self.MAPPING:
                getattr(self, self.MAPPING[choice])()
            elif choice == "q":
                break
            elif choice.isdigit():
                self.number_option_handler(choice)
            else:
                self.menu_options(choice)

    def menu_info(self):
        pass

    def number_options(self):
        pass

    def number_option_handler(self):
        MENU_LOGGER.info("Invalid choice")

    def menu_options(self, choice):
        MENU_LOGGER.info("Invalid choice")


class PagedMenu(Menu):
    MODEL = None

    def __init__(self, session, query=None):
        super().__init__(session)
        self.query = query if query is not None else select(self.MODEL)
        self.page = 1
        self.page_size = 5
        self.page_of_objects = []
        self.MAPPING.update({
            "n": "next_page",
            "p": "previous_page",
            "s": "sort",
        })
        self.load_page()

    def sort(self):
        MENU_LOGGER.info("Sort by:")
        MENU_LOGGER.info("1. Name")
        MENU_LOGGER.info("2. Rating")
        choice = input("Enter a choice: ")
        if choice == "1":
            self.query = self.query.order_by(self.MODEL.name)
        elif choice == "2":
            self.query = self.query.order_by(self.MODEL.rating.desc())

    def menu_info(self):
        for index, obj in enumerate(self.page_of_objects):
            MENU_LOGGER.info(f"{index + 1} - {obj}")

    def load_page(self):
        self.page_of_objects = list(self.session.scalars(self.query.limit(self.page_size)).all())

    def next_page(self):
        self.page += 1
        self.query = self.query.offset(self.page * self.page_size)
        self.load_page()

    def previous_page(self):
        self.page -= 1
        if self.page < 0:
            self.page = 0
        self.query = self.query.offset(self.page * self.page_size)
        self.load_page()


class ObjectMenu(Menu):

    def __init__(self, session, obj, object_index, parent):
        super().__init__(session, parent)
        self.object = obj
        self.object_index = object_index
        self.MAPPING.update({
            "n": "next_object",
            "p": "previous_object",
        })

    def next_object(self):
        self.object_index += 1
        try:
            self.object = self.parent.page_of_objects[self.object_index]
        except IndexError:
            LOGGER.warning("End of page of object, loading next page")
            self.parent.next_page()
            self.object_index -= self.parent.page_size
            self.object = self.parent.page_of_objects[self.object_index]

    def previous_object(self):
        self.object_index -= 1
        try:
            self.object = self.parent.page_of_objects[self.object_index]
        except IndexError:
            LOGGER.warning("End of page of object, loading next page")
            self.parent.previous_page()
            self.object_index += self.parent.page_size
            self.object = self.parent.page_of_objects[self.object_index]
