"""Script only for adding root directory to import universa."""
import sys
import os.path as op

ROOT_DIR = op.abspath(op.dirname(op.dirname(__file__)))

sys.path.append(ROOT_DIR)
