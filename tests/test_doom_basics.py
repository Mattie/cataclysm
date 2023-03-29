import pytest
from cataclysm import doom

# TODO Add a setup to clear the code cache

def test_add_numbers():
    # Positive test
    result = doom.add_numbers(5, 7)
    assert result == 12

    # Negative test, to ensure it's not always returning the same thing
    result = doom.add_numbers(-5, 7)
    assert result != 12

def test_multiply_numbers():
    # Positive test
    result = doom.multiply_numbers(3, 4)
    assert result == 12

    # Negative test, to ensure it's not always doing the same thing
    result = doom.multiply_numbers(3, 1)
    assert result != 12

def test_string_to_upper():
    # Positive test
    result = doom.string_to_upper("hello world")
    assert result == "HELLO WORLD"

    # Negative test, to ensure it's not always returning the same thing
    result = doom.string_to_upper("hello worlds")
    assert result != "HELLO WORLD"

def test_list_length():
    # Positive test
    result = doom.list_length([1, 2, 3, 4, 5])
    assert result == 5

    # Negative test, to ensure it's not always returning the same thing
    result = doom.list_length(['hello'])
    assert result != 5

def test_is_even():
    # Positive test
    result = doom.is_even(10)
    assert result == True

    # Positive test for odd number
    result = doom.is_even(7)
    assert result == False

    # Negative test for odd number
    result = doom.is_even(9)
    assert result != True

def test_sum_of_squares():
    # Test if doom can generate a function to calculate the sum of squares of a list of numbers
    # Positive test
    result = doom.sum_of_squares([1, 2, 3])
    assert result == 14

    # Negative test
    result = doom.sum_of_squares([2, 2, 3])
    assert result != 14

# To run tests, execute the command `pytest <filename>.py`