"""Compatibility wrapper for memory inspection utility."""

import os
import runpy
import sys

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
target = os.path.join(ROOT_DIR, "scripts", "inspect_memory.py")
sys.argv[0] = target
runpy.run_path(target, run_name="__main__")

