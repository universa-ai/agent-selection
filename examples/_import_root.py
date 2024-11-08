"""Script only for adding root directory to import universa."""
import sys
import os.path as op

sys.path.append(op.abspath(op.dirname(op.dirname(__file__))))
