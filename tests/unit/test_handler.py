"""
Tests
"""
import tempfile
import json
import os

from certbotwrapper import app


def test_symlinks():
    """
    Test symlink serialize/deserialize
    """
    with tempfile.TemporaryDirectory() as subject:
        os.chdir(subject)
        symlinks = [
            {"src": "csr/abc", "dst": "live/example.com/abc"},
            {"src": "csr/def", "dst": "live/example.com/def"},
            {"src": "csr/ghi", "dst": "live/example.com/ghi"},
        ]
        with open("symlinks.json", "w") as file:
            json.dump(symlinks, file)
        app.deserialize_symlinks()
        with open("live/README.txt", "w") as _:
            pass
        app.serialize_symlinks()

        with open("symlinks.json", "r") as file:
            assert symlinks == sorted(json.load(file), key=lambda item: item["dst"])
