import pytest
from cataclysm import doom

# TODO Add a setup to clear the code cache

# def _impending_exec_wrapper(*args_in, **kwargs_in):
#     global src
#     ldict = {'_exec_return_values': _exec_return_values,
#                 'args_in': args_in,
#                 'kwargs_in': kwargs_in}
#     # add all members of kwargs_in to ldict just in case
#     for k, v in kwargs_in.items():
#         ldict[k] = v
#     exec(src, ldict)
#     src = None # clean for next test
#     return ldict['_exec_return_values']

def test_impending_base():
    src = doom.impending.add_the_numbers(5, 7)
    assert src is not None
    assert type(src) == str or issubclass(type(src), str)  # might return ruamel.yaml.scalarstring.LiteralScalarString
    assert len(src) > 0
    assert "_exec_return_values" in src

# # TODO: Convert some of these to _impending to be sure returned code could be exec()'d
# def test_add_numbers():
#     # Positive test
#     result = doom..add_numbers(5, 7)
#     assert result == 12

#     # Negative test, to ensure it's not always returning the same thing
#     result = doom.add_numbers(-5, 7)
#     assert result != 12

# def test_multiply_numbers():
#     # Positive test
#     result = doom.multiply_numbers(3, 4)
#     assert result == 12

#     # Negative test, to ensure it's not always doing the same thing
#     result = doom.multiply_numbers(3, 1)
#     assert result != 12

# def test_string_to_upper():
#     # Positive test
#     result = doom.string_to_upper("hello world")
#     assert result == "HELLO WORLD"



# To run tests, execute the command `pytest <filename>.py`