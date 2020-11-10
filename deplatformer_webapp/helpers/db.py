from ..app import app, db


def get_collation_by_engine():
    with app.app_context():
        lookup = {
            # will raise without quoting
            "postgresql": "POSIX",
            # note MySQL databases need to be created w/ utf8mb4 charset
            # for the test suite
            "mysql": "utf8mb4_bin",
            "sqlite": "NOCASE",
            # will raise *with* quoting
            "mssql": "Latin1_General_CI_AS",
        }
        return lookup[db.get_engine().name]
