# this doesn't work
from ..doomed import *


def consume(globals_dict = globals()):
    """Consume globals in the cataclysm. Adds a new handler for globals() that will generate code for any function that isn't already defined."""
    builtins_dict = globals_dict['__builtins__']
    if isinstance(builtins_dict, types.ModuleType):
        builtins_dict = builtins_dict.__dict__
    globals_dict['__builtins__'] = InterceptDict(builtins.__dict__)
    print('[CATA] Globals consumed in the cataclysm.')
