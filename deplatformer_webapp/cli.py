import click
from flask_migrate import upgrade

from . import __version__
from .app import app


@click.group()
def cli():
    pass


@cli.command()
@click.option(
    "--host",
    default="0.0.0.0",
    help="Host to run the application on",
)
@click.option(
    "--port",
    default=5000,
    help="Port to run the application on",
)
def run(
    host,
    port,
):
    """Launches the app"""
    app.run(
        debug=False,
        host=host,
        port=port,
    )


@cli.command()
def version():
    """Displays web app version"""
    click.echo(f"Deplatformer WebApp - v{__version__}")


@cli.command()
def migratedb():
    """Creates database and applies migrations"""
    with app.app_context():
        upgrade()
