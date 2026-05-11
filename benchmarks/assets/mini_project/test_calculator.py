import pytest

from calculator import add, subtract, divide, average


def test_add():
    assert add(2, 3) == 5


def test_subtract():
    assert subtract(7, 3) == 4


def test_divide_by_zero_is_none():
    assert divide(10, 0) is None


def test_average_empty_is_zero():
    assert average([]) == 0
