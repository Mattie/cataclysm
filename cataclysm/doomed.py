import asyncio
import builtins
import datafiles
import hashlib
import inspect
import linecache
import os
import pkg_resources
import sys
import traceback
import types
from typing import Optional
from plunkylib import *
import loguru
logger = loguru.logger


@datafile("./datafiles/cataclysm/code/function_{self.name}.yml")
class Function:
    name: str
    signatures: Dict[str, str]

class CataclysmCreator:
    def __init__(self, autoexecute: bool = True, autogenerate: bool = True):
        self._autoexecute_ = autoexecute
        self._autogenerate_ = autogenerate
        if self._autoexecute_ and self._autogenerate_:
            # create a text-only version for the squeamish
            self.impending = CataclysmCreator(autoexecute=False, autogenerate=True)
            # create a version without more autogeneration for those who chose their fate
            self.chosen = CataclysmCreator(autoexecute=True, autogenerate=False)

    def __getattr__(self, method_name):
        """For any missing attribute, return our magic function to spread programmer dread."""

        # check self for attributes without using __getattr__
        if method_name in self.__dict__:
            return self.__dict__[method_name]

        def magic_method_creator(*args_in, **kwargs_in):
            calling_function_name = method_name

            # Gather inputs and their types
            inputs_info = []

            # # Add *args and **kwargs to inputs_info
            for i, arg_value in enumerate(args_in):
                inputs_info.append(f'args_in[{i}]-> {type(arg_value).__name__} = {arg_value}')
            for arg_name, arg_value in kwargs_in.items():
                inputs_info.append(f'kwargs_in["{arg_name}"]-> {type(arg_value).__name__} = {arg_value}')

            # Get installed modules information
            modules_info = self._get_installed_modules_info()
            stack_info = self._get_tracelines()

            # Format the information into text
            formatted_info = f"Function: {calling_function_name}\n"
            formatted_info += "Arguments:\n"
            formatted_info += "\n".join(inputs_info) + "\n"
            formatted_info += f"Call Stack:\n{stack_info}\n"
            formatted_info += "Installed Modules:\n" + "|".join(modules_info) + "\n"

            code_signature = self._build_function_signature(calling_function_name, args_in, kwargs_in)

            # Generate the code
            code = self._conjure_code(calling_function_name, code_signature, formatted_info)
            if code is None:
                # No code available for this function, likely using .chosen
                raise NameError(f"No code for function {calling_function_name} with signature {code_signature}")

            # exec the code with locals() and globals()
            if self._autoexecute_:
                try:
                    # Execute the code
                    _exec_return_values = None
                    # deep copy of locals
                    ldict = {'_exec_return_values': _exec_return_values,
                            'args_in': args_in,
                            'kwargs_in': kwargs_in}
                    # add all members of kwargs_in to ldict just in case
                    for k, v in kwargs_in.items():
                        ldict[k] = v
                    exec(code, ldict)
                except Exception as e:
                    print("Error in code execution, trying again...")
                    formatted_info += "\n\nThe following code does not work and we need a new method to avoid the error traceback below.\nErrored code:\n"
                    formatted_info += code
                    # output the error trace as if the code was inside this method
                    #traceback.print_exc()
                    # get the traceback string
                    tb = traceback.format_exc()
                    # try one more time to regenerate the code
                    formatted_info += f"\n\nEnsure your code is robust enough or entirely different to avoid this error (from the last code I tried): {e}\n"
                    formatted_info += f"\nError Traceback: {tb}\n"
                    code = self._conjure_code(calling_function_name, code_signature, formatted_info, retry=True)
                    try:
                        # exec the code with locals() and globals()
                        exec(code, ldict)
                    except Exception as e:
                        # output the error trace as if the code was inside this method
                        traceback.print_exc()
                        # raise the exception
                        raise e
                return ldict['_exec_return_values']
            else:
                return code
        return magic_method_creator

    def _build_function_signature(self, calling_function_name, args_in, kwargs_in):
        """Create a unique string for the function signature."""
        # signature string starts with the function name + the number of arguments
        signature = f"{calling_function_name}-{len(args_in)}-{len(kwargs_in)}"
        # + the type of each argument (kwarg or arg)
        for arg in args_in:
            signature += f"-{type(arg).__name__}"
        for arg in kwargs_in:
            signature += f"-{type(arg).__name__}"
        # + the keyword argument names
        for arg in kwargs_in:
            signature += f"-{arg}"
        return signature

    def _lookup_old_code(self, funcname, signature):
        """Lookup code based on the given signature and function name."""
        func_obj = Function.objects.get_or_none(name=funcname)
        if func_obj is not None:
            if func_obj.signatures is None:
                func_obj.signatures = {}
            doomed_code = func_obj.signatures.get(signature, None)
        else:
            doomed_code = None
        return doomed_code
    
    def _save_conjured_code(self, funcname, signature, code):
        """Save the code to the datafile store."""
        func_obj = Function.objects.get_or_none(name=funcname)
        if func_obj is None:
            func_obj = Function(name=funcname, signatures={})
        if func_obj.signatures is None:
            func_obj.signatures = {}
        func_obj.signatures[signature] = code
        func_obj.datafile.save()

    def _generate_fresh_code(self, formatted_info):
        """Generate fresh code using OpenAI given formatted_info to use in the prompt."""
        # use plunkylib for the query
        ai_query = Petition.objects.get("CataclysmQuery")
        ai_query.load_all()
        args = {}
        args['arg1'] = formatted_info
        # we're not an async function, so we can't use await, so we can have asyncio run the function for us
        completion_result, adj_prompt_text = asyncio.run(petition_completion2(petition=ai_query, additional=args, content_filter_check=False))
        # take the resulting text and get the code after #|~~
        fresh_code = completion_result.text.split("#|~~\n")[1]
        return fresh_code

    def _conjure_code(self, funcname, signature, formatted_info, retry=False):
        """
        Generate code based on the given hash, function name, and formatted information.

        :param hash: Hash value of the code snippet
        :param funcname: Function name of the code snippet
        :param formatted_info: Formatted information for the code generation
        :param retry: Flag to retry code generation if the previous attempt failed
        :return: Generated code snippet
        """
        doomed_code = self._lookup_old_code(funcname, signature)
        
        # without autogeneration we're done here
        if not self._autogenerate_:
            return doomed_code
        
        # unless retrying, conjure up the existing code
        if not retry and doomed_code is not None:
            return doomed_code

        # generate fresh code
        fresh_code = self._generate_fresh_code(formatted_info)

        # log the code str, but each line will be prefixed by an extra #
        loginfo = f"Doomed code:\n{'## '.join(fresh_code.splitlines(True))}"
        logger.debug(loginfo)

        # add the code to the cached code store
        self._save_conjured_code(funcname, signature, fresh_code)

        return fresh_code

    def _get_installed_modules_info(self):
        installed_modules = []
        for module in pkg_resources.working_set:
            installed_modules.append(f"{module.project_name} ({module.version})")

        return installed_modules

    def _get_tracelines(self, lines_before=2, lines_after=1, stack_depth=5, stack_skip_recent=1):
        """
        Get source lines and docstrings for the current call stack.

        :param lines_before: Number of lines before the current line to include
        :param lines_after: Number of lines after the current line to include
        :param stack_depth: Number of stack frames to include
        :param stack_skip_recent: Number of most recent stack frames to skip
        :return: List of source lines and docstrings
        """
        current_stack = inspect.stack()[stack_skip_recent:stack_depth + stack_skip_recent]

        source_lines = []

        for frame_info in current_stack:
            filename = frame_info.filename
            lineno = frame_info.lineno
            function_name = frame_info.function

            # Get lines_before and lines_after for the current line number
            start_line = max(1, lineno - lines_before)
            end_line = lineno + lines_after

            # Extract lines from the source file
            lines = [linecache.getline(filename, i).rstrip() for i in range(start_line, end_line + 1)]

            # Get the function, class, or method object
            obj = frame_info.frame.f_globals.get(function_name)

            # Get the docstring for the function, class, or method
            docstring = None
            if obj is not None:
                docstring = inspect.getdoc(obj)

            # Combine the lines and add them to the source_lines list
            source_lines.append(f"{filename} (lines {start_line}-{end_line}):")
            if docstring:
                source_lines.append(f"\ndocstring: {docstring}")
            source_lines.append("\n".join(lines))
        return source_lines
    

class InterceptFunction:
    """Proxy for function objects that, when called, generates likely code."""
    def __init__(self, name):
        self.name = name
        self.doom = CataclysmCreator()

    def __call__(self, *args, **kwargs):
        """Intercept function call."""
        return self.doom.__getattr__(self.name)(*args, **kwargs)

class InterceptDict(dict):
    def __getitem__(self, key):
        """Intercept dictionary access."""
        try:
            value = super().__getitem__(key)
        except KeyError:
            value = InterceptFunction(key)
            self[key] = value
        return value

# the cataclysm doom object
doom = CataclysmCreator()
