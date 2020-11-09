from pathlib import Path  # Python 3.6+ only

import click
from click.decorators import pass_context
from dotenv import load_dotenv
from flask_migrate import upgrade, migrate

from . import __version__


@click.group()
@click.option(
    "--env-file", help="Environment file to use",
)
@pass_context
def cli(ctx, env_file):
    if env_file is not None:
        env_path = Path(".") / env_file
        if env_path.is_file():
            load_dotenv(dotenv_path=env_path)
        else:
            raise click.FileError(str(env_path))


@cli.command()
@click.option(
    "--host", default="0.0.0.0", help="Host to run the application on",
)
@click.option(
    "--port", default=5000, help="Port to run the application on",
)
@click.option(
    "--debug", is_flag=True
)
def run(host, port, debug):
    """Launches the app"""
    from .app import app
    app.run(
        debug=debug, host=host, port=port,
    )


@cli.command()
def version():
    """Displays web app version"""
    click.echo(f"Deplatformer WebApp - v{__version__}")


@cli.command()
def migratedb():
    """Creates database and applies migrations"""
    from .app import app

    with app.app_context():
        upgrade(directory="migrations/{0}".format(app.config["ENV"]))

@cli.command()
def dropdb():
    """Removes everything from the database. Use with CAUTION!"""
    from .app import app, db

    with app.app_context():
        db.drop_all()

@cli.command()
def makemigrations():
    """Creates migrations"""
    from .app import app

    with app.app_context():
        migrate(directory="migrations/{0}".format(app.config["ENV"]))
