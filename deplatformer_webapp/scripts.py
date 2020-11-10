# This is a temporary workaround till Poetry supports scripts, see
# https://github.com/sdispater/poetry/issues/241.
from subprocess import CalledProcessError, check_call


def format() -> None:
    check_call(
        ["isort deplatformer_webapp tests && black ."],
        shell=True,
    )


def lint() -> None:
    try:
        check_call(["flakehell", "lint", "."])
    except CalledProcessError:
        # ignore non zero exit code
        pass
