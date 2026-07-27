# The only column types STRICT tables accept: <https://www.sqlite.org/stricttables.html>
STRICT_TYPES = frozenset({"int", "integer", "real", "text", "blob", "any"})

# A REAL (IEEE 754 double) maxes out at 15.95 significant digits, so 15 is a safe limit.
# <https://sqlite.org/floatingpoint.html>
REAL_EXACT_DIGITS = 15
