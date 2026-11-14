"""check_text_safety: an escaped currency sign \\$ is not a math delimiter (issue 399615)."""

import pytest

from math_engine.verify import check_text_safety


def test_escaped_dollar_inside_math_is_balanced():
    check_text_safety("Q1", "prompt", r"A ticket costs $\$12$ and a pass costs $\$45$.")


def test_unbalanced_delimiter_still_fails():
    with pytest.raises(Exception, match="unbalanced"):
        check_text_safety("Q1", "prompt", r"A ticket costs $\$12 and a pass costs $45$.")


def test_latex_field_allows_escaped_dollar_but_not_delimiters():
    check_text_safety("Q1", "display", r"C = \$12 n + \$45", is_latex=True)
    with pytest.raises(Exception, match="must not contain"):
        check_text_safety("Q1", "display", r"$C = 12n$", is_latex=True)
