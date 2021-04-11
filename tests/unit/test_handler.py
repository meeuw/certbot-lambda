import pytest
import tempfile
import textwrap
import json
import os

from certbotwrapper import app


def test_symlinks():
    with tempfile.TemporaryDirectory() as subject:
        os.chdir(subject)
        symlinks = [
            {"src": "csr/abc", "dst": "live/example.com/abc"},
            {"src": "csr/def", "dst": "live/example.com/def"},
            {"src": "csr/ghi", "dst": "live/example.com/ghi"},
        ]
        with open("symlinks.json", "w") as f:
            json.dump(symlinks, f)
        app.deserialize_symlinks()
        with open("live/README.txt", "w") as f:
            pass
        app.serialize_symlinks()

        with open("symlinks.json", "r") as f:
            assert symlinks == sorted(json.load(f), key=lambda item: item["dst"])
