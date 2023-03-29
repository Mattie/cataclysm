import pytest
from cataclysm import doom

# TODO Add a setup to clear the code cache

# TODO: We can get coverage of the retry method this way but can't be 100% sure it worked. 
#       Need to find a way to test the retry method itself.

def test_throw_ZeroDivisionError():
    try:
        doom.force_raise_ZeroDivisionError()
    except ZeroDivisionError:
        assert True
    except Exception:
        # anything else is bad
        assert False
    else:    
        # we tell it to retry and not fail so technically it's a pass
        assert True

# To run tests, execute the command `pytest <filename>.py`