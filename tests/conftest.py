import pytest

from uniparser_yawarana import YawaranaAnalyzer


@pytest.fixture
def parser():
    a = YawaranaAnalyzer()
    return a
