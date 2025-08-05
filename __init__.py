"""
Code Analyzer Package
=====================

This package contains a simple static analysis tool that can be used to
evaluate source code for complexity, adherence to coding style guidelines and
software design principles.  The primary entry point is the CLI implemented
in ``main.py``; however the ``metrics`` and ``principles`` modules can also
be imported directly from Python code to build custom tooling.

Example::

    from code_analyzer.metrics import analyse_directory
    from code_analyzer.principles import evaluate_solid

    files = analyse_directory("path/to/my_project")
    solid = evaluate_solid(files)

"""

from .metrics import analyse_directory, FileMetrics  # re-export for convenience
from .principles import evaluate_solid, evaluate_functional

__all__ = [
    "analyse_directory",
    "FileMetrics",
    "evaluate_solid",
    "evaluate_functional",
]
