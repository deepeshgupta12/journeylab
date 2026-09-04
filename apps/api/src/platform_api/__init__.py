"""Public platform surface — STEP-007.

NAMED `platform_api` AND NOT `platform`, WHICH WAS THE FIRST ATTEMPT
    `apps/api/src` is on `pythonpath`, so a package called `platform` shadows the
    standard library's — and `platform.system()` is called by enough libraries that
    the failure would have surfaced somewhere unrelated, as an import error in a
    dependency. Caught by importing it before writing a line of the handler.
"""
