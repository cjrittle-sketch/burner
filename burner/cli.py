"""Console-script entry point for the `pc` command.

The real implementation lives in bin/pc (a python3 script). This wrapper
locates it and execs it, so `pip install .` / `pip install -e .` produces a
working `pc` command while keeping a single source of truth for the CLI.
"""
import os
import sys


def _pc_script():
    here = os.path.dirname(os.path.realpath(__file__))
    # Installed layout guesses, in order of likelihood:
    candidates = [
        # Editable / source-tree install: burner/cli.py sits next to bin/.
        os.path.join(os.path.dirname(here), "bin", "pc"),
        # Regular install: look next to the interpreter's prefix (rare).
        os.path.join(sys.prefix, "bin", "pc"),
    ]
    for c in candidates:
        if os.path.isfile(c):
            return c
    return None


def main(argv=None):
    script = _pc_script()
    if script is None:
        print(
            "burner: could not find bin/pc next to this package. "
            "If you installed from a source checkout, run `pip install -e .` "
            "from the repo root.",
            file=sys.stderr,
        )
        return 1
    args = [sys.executable or "python3", script] + (sys.argv[1:] if argv is None else argv)
    os.execv(args[0], args)
