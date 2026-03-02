from sqlmodel import Session, SQLModel, create_engine

from foundry.settings import get_settings

settings = get_settings()
connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, echo=False, connect_args=connect_args)


def init_db() -> None:
    SQLModel.metadata.create_all(engine)
    from foundry.services.template_seed import seed_default_templates

    with Session(engine) as session:
        seed_default_templates(session)


def get_session():
    with Session(engine) as session:
        yield session
