import os
from pathlib import Path  # Python 3.6+ only

import click
from click.decorators import pass_context
from dotenv import load_dotenv
from flask_migrate import migrate, upgrade

from . import __version__
from .helpers import is_docker_running
from .helpers.ipfs import register_ipfs_daemon_exit_handler, run_docker_ipfs_daemon


@click.group()
@click.option(
    "--env-file",
    help="Environment file to use",
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
    "--host",
    default="0.0.0.0",
    help="Host to run the application on",
)
@click.option(
    "--port",
    default=5000,
    help="Port to run the application on",
)
@click.option("--debug", is_flag=True)
@pass_context
def run(ctx, host, port, debug):
    """Launches the app"""
    if not is_docker_running():
        print("Coulnd't initiate IPFS daemon. Are you sure you have docker daemon installed and running?")
        exit(1)

    from .app import app

    ipfs_container = run_docker_ipfs_daemon(app.config["IPFS_STAGING_DIR"], app.config["IPFS_STAGING_DIR"])
    register_ipfs_daemon_exit_handler(ipfs_container)

    ctx.invoke(migratedb)

    app.run(
        debug=debug,
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
    from .app import app

    with app.app_context():
        cwd = os.path.abspath(os.path.dirname(__file__))
        upgrade(directory=os.path.join(cwd, "migrations"))


@cli.command()
def deletedb():
    """Deletes db file"""
    from .app import app

    os.remove(os.path.join(app.config["BASEDIR"], app.config["SQLITE_DB"]))
    click.echo(f"Database deleted successfully!")


@cli.command()
def makemigrations():
    """Creates migrations"""
    from .app import app

    with app.app_context():
        migrate(directory="migrations/{0}".format(app.config["ENV"]))
