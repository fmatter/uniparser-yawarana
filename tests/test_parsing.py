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


def test_hello(parser):
    assert parse_1("sujtase", parser).lemma == "sujta"
