import pytest


@pytest.fixture
def temporary_file(tmp_path):
    p = tmp_path / "hello.txt"
    p.write_text("Hello World!")
    return p
