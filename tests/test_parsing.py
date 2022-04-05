"""Tests for the uniparser_yawarana.my_module module.
"""
import pytest

from uniparser_yawarana import YawaranaAnalyzer


@pytest.fixture
def parser():
    a = YawaranaAnalyzer()
    return a


def parse_1(str, parser):
    return parser.analyze_words(str)[0]


def test_se(parser):
    for a, b in [("sujta", "sujtase")]:
        assert parse_1(b, parser).lemma == a


def test_clitics(parser):
    assert parse_1("yatampe", parser).lemma == "yatanë"
    assert parse_1("chawë", parser).lemma == "chi"

def test_multiple(parser):
    assert len(parser.analyze_words("wïrë tawara rë entë".split(" "))) == 4


def test_bad_parsing(parser):
    assert len(parser.analyze_words("yawë", parser)) == 1
