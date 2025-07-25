# Copyright (c) 2015 Universidade Federal Fluminense (UFF)
# Copyright (c) 2015 Polytechnic Institute of New York University.
# This file is part of noWorkflow.
# Please, consult the license terms in the LICENSE file.
"""Test now.cross_version module"""
from __future__ import (absolute_import, print_function,
                        division, unicode_literals)

import unittest
from ..now.utils.cross_version import cross_compile, PY310


class TestCrossVersion(unittest.TestCase):
    """TestCase for now.cross_version module"""

    def test_cross_compile(self):
        """Check if cross_compile behavior matches compile behavior"""
        code = b"a = 2"
        expected = compile(code, "name", "exec")
        result = cross_compile(code, "name", "exec")
        args = [
            "co_argcount", "co_cellvars", "co_code", "co_consts",
            "co_filename", "co_firstlineno", "co_freevars", 
            "co_name", "co_names", "co_nlocals", "co_stacksize", "co_varnames"
        ]
        if not PY310:
            args.append("co_lnotab")
        # ToDo: maybe check method co_lines on Python > 3.10

        for arg in args:
            self.assertEqual(getattr(expected, arg), getattr(result, arg))
        # On Python 2: result.co_flags != expected.co_flags
