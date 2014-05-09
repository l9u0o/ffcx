
import os
from uflacs.utils.log import info, warning

def add_compile_dolfin_options(opts):
    "Args: list of .ufl file(s)."
    pass

def run_compile_dolfin(options, args):
    "Compile expressions from .ufl file(s) into dolfin C++ Expressions."
    from ufl.algorithms import load_ufl_file
    from uflacs.backends.dolfin.compiler import compile_dolfin_expressions_header

    for input_filename in args:
        prefix, ext = os.path.splitext(os.path.basename(input_filename))
        if ext != '.ufl':
            warning("Expecting ufl file, got %s." % ext)
        output_filename = prefix + '.h'

        info("Loading file '%s'..." % (input_filename,))
        data = load_ufl_file(input_filename) # FIXME: Don't want preprocessing here
        info("Compiling '%s'..." % prefix)
        code = compile_dolfin_expressions_header(data.expressions,
                                                 data.object_names,
                                                 prefix)
        info("Writing code to '%s'..." % output_filename)
        with open(output_filename, "w") as f:
            f.write(code)

    return 0
