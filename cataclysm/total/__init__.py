import builtins
import inspect
import types

from ..doomed import InterceptDict


def consume(globals_dict=None):
    """Intercept unresolved functions in the given or caller's global namespace."""
    if globals_dict is None:
        frame = inspect.currentframe()
        if frame is None or frame.f_back is None:
            raise RuntimeError("Could not determine the caller's global namespace.")
        try:
            globals_dict = frame.f_back.f_globals
        finally:
            del frame

    builtins_dict = globals_dict.get("__builtins__", builtins)
    if isinstance(builtins_dict, types.ModuleType):
        builtins_dict = builtins_dict.__dict__
    globals_dict["__builtins__"] = InterceptDict(builtins_dict)
    print("[CATA] Globals consumed in the cataclysm.")
