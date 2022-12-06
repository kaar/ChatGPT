import dbm
import json
import os

XDG_CACHE_HOME = os.environ.get("XDG_CACHE_HOME", os.path.expanduser("~/.cache"))


class DbmCache:
    def __init__(self, cache_file: str):

        if not os.path.exists(cache_file):
            os.makedirs(os.path.dirname(cache_file), exist_ok=True)

        self.cache_file = cache_file

    def get(self, key: str):
        with dbm.open(self.cache_file, "c") as db:
            if key in db:
                return json.loads(db[key])
        return None

    def set(self, key: str, value: dict):
        with dbm.open(self.cache_file, "c") as db:
            db[key] = json.dumps(value)

    def drop(self, key: str):
        with dbm.open(self.cache_file, "c") as db:
            if key in db:
                del db[key]

    def list(self):
        with dbm.open(self.cache_file, "c") as db:
            return list(db.keys())
