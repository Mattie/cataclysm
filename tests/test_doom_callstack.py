import pytest
from cataclysm import doom

# TODO Add a setup to clear the code cache
def level_19(x):
    """ We have docstrings in each of these to make things interesting"""
    return doom.log_base7_of(x)

def level_18(x):
    """ We have docstrings in each of these to make things interesting"""
    return level_19(x)

def level_17(x):
    """ We have docstrings in each of these to make things interesting"""
    return level_18(x)

def level_16(x):
    """ We have docstrings in each of these to make things interesting"""
    return level_17(x)

def level_15(x):
    """ We have docstrings in each of these to make things interesting"""
    return level_16(x)

def level_14(x):
    """ We have docstrings in each of these to make things interesting"""
    return level_15(x)

def level_13(x):
    """ We have docstrings in each of these to make things interesting"""
    return level_14(x)

def level_12(x):
    """ We have docstrings in each of these to make things interesting"""
    return level_13(x)

def level_11(x):
    """ We have docstrings in each of these to make things interesting"""
    return level_12(x)

def level_10(x):
    """ We have docstrings in each of these to make things interesting"""
    return level_11(x)

def level_9(x):
    """ We have docstrings in each of these to make things interesting"""
    return level_10(x)

def level_8(x):
    """ We have docstrings in each of these to make things interesting"""
    return level_9(x)

def level_7(x):
    """ We have docstrings in each of these to make things interesting"""
    return level_8(x)

def level_6(x):
    """ We have docstrings in each of these to make things interesting"""
    return level_7(x)

def level_5(x):
    """ We have docstrings in each of these to make things interesting"""
    return level_6(x)

def level_4(x):
    """ We have docstrings in each of these to make things interesting"""
    return level_5(x)

def level_3(x):
    """ We have docstrings in each of these to make things interesting"""
    return level_4(x)

def level_2(x):
    """ We have docstrings in each of these to make things interesting"""
    return level_3(x)

def level_1(x):
    """ We have docstrings in each of these to make things interesting"""
    return level_2(x)

def test_deep_call_stack():
    # Test if doom can generate a function that performs a simple calculation correctly despite the deep call stack

    # Positive test
    result = level_1(99)
    assert int(result) == 2

    # Negative test, to ensure it's not always returning the same thing
    result = level_1(9999)
    assert int(result) != 2
