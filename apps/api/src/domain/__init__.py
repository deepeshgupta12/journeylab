"""Canonical domain model — STEP-006.

A package rather than a bare module directory because every sibling under
`apps/api/src` is one (`auth`, `authz`, `conventions`, `generated`) and mypy
resolves this tree by package. The opposite mistake was made in STEP-005.05, where
a services root got an `__init__.py` its siblings did not have; the rule is to
match the tree you are in, not a habit.
"""
