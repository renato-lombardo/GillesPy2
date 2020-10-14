
"""
This file contains a function and variable for testing a machines support of GillesPy2 C++ solvers.
Used in model.py
"""


def check_cpp_support():
    import shutil;

    dependencies = ['g++', 'make']
    missing = []
    any_missing = False

    for dependency in dependencies:
        if shutil.which(dependency) != None:
            continue

        missing.append(dependency)
        any_missing = True

    if any_missing is True:
        from gillespy2.core import log
        log.warn('Unable to use C++ optimized SSA due to one or more missing dependencies: {0}. '
        'The performance of this package can be significantly increased if you install/configure '
        'these on your machine.'.format(missing))

    return not any_missing

    """
    from gillespy2.solvers.cpp.example_models import Example
    from gillespy2 import SSACSolver
    try:
        model = Example()
        results = model.run(solver=SSACSolver, cpp_support=True)
        return True
    except Exception as e:
        log.warn('Unable to use C++ optimized SSA: {0}.  The performance of ' \
        'this package can be significantly increased if you install/configure GCC on ' \
        'this machine.'.format(e))
        return False
    """

cpp_support = check_cpp_support()
