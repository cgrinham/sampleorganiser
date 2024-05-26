import os
import logging

import sqlalchemy as sa
import sqlalchemy.orm
from sqlalchemy import select
import playsound

import models

MENU_LOGGER = logging.getLogger('sample_organiser/menu')
LOGGER = logging.getLogger('sample_organiser')


AUTO_TAG_CACHE = []


def load_tag_filter_cache(session):
    if not AUTO_TAG_CACHE:
        tags_query = select(models.Tag).options(sa.orm.joinedload(models.Tag.filters))
        for tag in session.scalars(tags_query).unique():
            AUTO_TAG_CACHE.append(tag)


def auto_tag_sample(session, sample):
    load_tag_filter_cache(session)

    LOGGER.info(f"Auto tagging sample: {sample.filename} from {len(AUTO_TAG_CACHE)} tags")

    for tag in AUTO_TAG_CACHE:
        LOGGER.info(f"{tag}: {tag.filters}")
        if not tag.filters:
            continue
        LOGGER.info(tag)
        for tag_filter in tag.filters:
            LOGGER.info(tag_filter.string)
            if tag_filter.string in sample.filename.lower():
                LOGGER.info(f"Tag found: {tag.name} - {sample.filename}")
                sample.tags.append(tag)
                break


def find_samples_in_dir(session, path):
    # Get all the files in the directory
    added = 0
    for root, _, files in os.walk(path):
        for file in files:
            if not file.endswith(".wav"):
                continue
            file_path = os.path.join(root, file)
            # Check if the file is already in the database
            sample_query = select(models.Sample).where(models.Sample.path == file_path)

            if session.execute(sample_query).first():
                continue

            sample = models.Sample(name=file, path=file_path)
            session.add(sample)
            session.flush()
            auto_tag_sample(session, sample)
            added += 1
            LOGGER.info(sample)
    MENU_LOGGER.info("-----")
    MENU_LOGGER.info(f"Added {added} samples")
    MENU_LOGGER.info("-----")
    return


def play_sample(sample):
    MENU_LOGGER.info(f"Play sample: {sample.path}")
    playsound.playsound(sample.path)

    MENU_LOGGER.info("---------")
    MENU_LOGGER.info("Playing finished")
    MENU_LOGGER.info("---------")
