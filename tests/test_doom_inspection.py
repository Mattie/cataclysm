import pytest
from cataclysm import doom

# TODO Add a setup to clear the code cache

# NOTE: This test file is testing inspection of keyword args, comments and docstrings.
# As such, the specific comments and docstrings below are important to the tests.


def test_comment_stuff():
    # Validate whether two numbers are both divisible by 17
    result = doom.do__helper(34, 51)
    assert result == True

    # Negative test, to ensure it's not always returning the same thing
    result = doom.do__helper(3, 51)
    assert result != True

def test_more_comments():
    # Append the string representations of two numbers to each other
    result = doom.do__helper2(34, 51)
    assert result == '3451'

    # Negative test, to ensure it's not always returning the same thing
    result = doom.do__helper(3, 51)
    assert result != '3451'

def test_doc_stuff():
    def _asdf(p, q):
        return doom._n_helper(p, q)

    def _qwer(x, y):
        """ We need to return the sum of two numbers"""
        return _asdf(x, y)
    
    # Positive test
    result = _qwer(5, 7)
    assert result == 12

    # Negative test, to ensure it's not always returning the same thing
    result = _qwer(-5, 7)
    assert result != 12

def test_ka():
    result = doom.do__helper4(dividend=75, divisor=9, remainder_only=True)
    assert result == 3
