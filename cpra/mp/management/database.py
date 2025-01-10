from sqlmodel import SQLModel, create_engine

from cpra.mp.management.settings import settings

engine = create_engine(settings.db_url)


def create_all():
    SQLModel.metadata.create_all(engine)
