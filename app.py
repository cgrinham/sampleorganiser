import logging

from sqlalchemy.orm import Session
from cli.main import MainMenu
import db
import audio

# logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger('sample_organiser')
LOGGER.setLevel("INFO")
ROOT_LOG_FORMATTER = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# LOGGER.setFormatter(ROOT_LOG_FORMATTER)
MENU_LOGGER = logging.getLogger('sample_organiser/menu')
MENU_LOGGER.handlers.clear()
MENU_LOG_FORMATTER = logging.Formatter('%(message)s')
MENU_LOG_HANDLER = logging.StreamHandler()
MENU_LOG_HANDLER.setFormatter(MENU_LOG_FORMATTER)
MENU_LOGGER.addHandler(MENU_LOG_HANDLER)
MENU_LOGGER.setLevel("INFO")

AUDIO_LOGGER = logging.getLogger('sample_organiser/audio')
AUDIO_LOGGER.setLevel("INFO")


def main():
    audio.set_up_client()
    with Session(db.engine) as session:
        menu = MainMenu(session)
        menu.run()


if __name__ == __name__:
    db.Base.metadata.create_all(db.engine)
    main()
