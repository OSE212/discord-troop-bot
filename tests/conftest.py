import pytest

from bot.database.base import Database
from bot.database.repositories.player_repository import PlayerRepository
from bot.rules.configuration import default_config
from bot.services.formation_service import FormationService
from bot.services.player_service import PlayerService


@pytest.fixture()
def db():
    database = Database("sqlite:///:memory:")
    database.create_all()
    return database


@pytest.fixture()
def session(db):
    with db.session() as s:
        yield s


@pytest.fixture()
def repository(session):
    return PlayerRepository(session)


@pytest.fixture()
def player_service(repository):
    return PlayerService(repository)


@pytest.fixture()
def config():
    return default_config()


@pytest.fixture()
def formation_service(repository, config):
    return FormationService(repository, config)
