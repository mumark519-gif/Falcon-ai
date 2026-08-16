from __future__ import annotations

import ast
import math
import operator
import re
from typing import Any


# ============================================================
# SAFE AST OPERATORS
# ============================================================

_ALLOWED_BINARY_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}

_ALLOWED_UNARY_OPERATORS = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}


# ============================================================
# SAFE EXPRESSION EVALUATOR
# ============================================================

def _safe_eval_expression(
    expression: str,
) -> Any:
    """
    Evaluate a mathematical expression using a restricted AST.

    Supported:
        +  -  *  /  //  %  **
        unary +/-
        integers
        floats
        parentheses

    No imports, attributes, function calls, variables, or
    arbitrary Python execution are permitted.
    """

    expression = str(
        expression or ""
    ).strip()

    if not expression:
        raise ValueError(
            "Mathematical expression is empty."
        )

    tree = ast.parse(
        expression,
        mode="eval",
    )

    def evaluate(
        node: ast.AST,
    ) -> Any:

        # ----------------------------------------------------
        # Expression
        # ----------------------------------------------------

        if isinstance(
            node,
            ast.Expression,
        ):
            return evaluate(
                node.body
            )

        # ----------------------------------------------------
        # Numeric constants
        # ----------------------------------------------------

        if isinstance(
            node,
            ast.Constant,
        ):

            if isinstance(
                node.value,
                bool,
            ):
                raise ValueError(
                    "Boolean values are not valid mathematical operands."
                )

            if isinstance(
                node.value,
                (int, float),
            ):
                return node.value

            raise ValueError(
                "Only numeric constants are allowed."
            )

        # ----------------------------------------------------
        # Binary operations
        # ----------------------------------------------------

        if isinstance(
            node,
            ast.BinOp,
        ):

            operator_type = type(
                node.op
            )

            operation = (
                _ALLOWED_BINARY_OPERATORS.get(
                    operator_type
                )
            )

            if operation is None:
                raise ValueError(
                    "Unsupported mathematical operator."
                )

            left = evaluate(
                node.left
            )

            right = evaluate(
                node.right
            )

            # Prevent pathological exponentiation.
            if (
                operator_type is ast.Pow
                and isinstance(
                    right,
                    (int, float),
                )
                and abs(right) > 10000
            ):
                raise ValueError(
                    "Exponent is too large."
                )

            result = operation(
                left,
                right,
            )

            return result

        # ----------------------------------------------------
        # Unary operations
        # ----------------------------------------------------

        if isinstance(
            node,
            ast.UnaryOp,
        ):

            operator_type = type(
                node.op
            )

            operation = (
                _ALLOWED_UNARY_OPERATORS.get(
                    operator_type
                )
            )

            if operation is None:
                raise ValueError(
                    "Unsupported unary operator."
                )

            return operation(
                evaluate(
                    node.operand
                )
            )

        # ----------------------------------------------------
        # Everything else is forbidden.
        # ----------------------------------------------------

        raise ValueError(
            "Expression contains an unsupported operation."
        )

    return evaluate(
        tree
    )


# ============================================================
# QUESTION EXTRACTION
# ============================================================

def _extract_factorial(
    text: str,
) -> int | None:
    """
    Extract factorial requests such as:

        25 factorial
        factorial of 25
        25!
        what is 25 factorial?
    """

    patterns = (
        r"\b(\d+)\s*!",
        r"\b(\d+)\s+factorial\b",
        r"\bfactorial\s+of\s+(\d+)\b",
    )

    for pattern in patterns:

        match = re.search(
            pattern,
            text,
            flags=re.IGNORECASE,
        )

        if not match:
            continue

        value = int(
            match.group(1)
        )

        if value < 0:
            raise ValueError(
                "Factorial requires a non-negative integer."
            )

        if value > 100000:
            raise ValueError(
                "Factorial input is too large."
            )

        return value

    return None


def _extract_percentage(
    text: str,
) -> tuple[float, float] | None:
    """
    Extract simple percentage requests.

    Examples:

        20% of 500
        what is 15 percent of 200
    """

    patterns = (
        r"(\d+(?:\.\d+)?)\s*%\s*(?:of)\s*(\d+(?:\.\d+)?)",
        r"(\d+(?:\.\d+)?)\s*percent\s*(?:of)\s*(\d+(?:\.\d+)?)",
    )

    for pattern in patterns:

        match = re.search(
            pattern,
            text,
            flags=re.IGNORECASE,
        )

        if not match:
            continue

        percentage = float(
            match.group(1)
        )

        number = float(
            match.group(2)
        )

        return (
            percentage,
            number,
        )

    return None


# ============================================================
# GENERATED PYTHON DETECTION
# ============================================================

def _extract_generated_python_factorial(
    source: str,
) -> int | None:
    """
    Recognize the safe Python source generated by Falcon's
    deterministic planner for factorial calculations.

    Supported examples:

        import math; print(math.factorial(25))
        print(math.factorial(25))
        result = math.factorial(25); print(result)

    This does NOT execute Python source.

    Instead, the source is parsed and the mathematical operation
    is extracted and executed through Falcon's safe evaluator /
    deterministic math implementation.
    """

    source = str(
        source or ""
    ).strip()

    if not source:
        return None

    patterns = (
        r"math\.factorial\s*\(\s*(\d+)\s*\)",
        r"factorial\s*\(\s*(\d+)\s*\)",
    )

    for pattern in patterns:

        match = re.search(
            pattern,
            source,
            flags=re.IGNORECASE,
        )

        if not match:
            continue

        value = int(
            match.group(1)
        )

        if value < 0:
            raise ValueError(
                "Factorial requires a non-negative integer."
            )

        if value > 100000:
            raise ValueError(
                "Factorial input is too large."
            )

        return value

    return None


def _extract_generated_python_expression(
    source: str,
) -> str | None:
    """
    Recognize simple arithmetic expressions embedded in
    deterministic Python generated by Falcon.

    Supported examples:

        print(25 * 5)
        result = 100 / 4; print(result)
        print((10 + 5) * 2)

    The expression is still evaluated through the restricted
    AST evaluator. No arbitrary Python code is executed.
    """

    source = str(
        source or ""
    ).strip()

    if not source:
        return None

    # --------------------------------------------------------
    # print(<expression>)
    # --------------------------------------------------------

    match = re.fullmatch(
        r"\s*(?:print)\s*\(\s*([0-9\s\.\+\-\*\/\%\(\)]+)\s*\)\s*;?\s*",
        source,
        flags=re.IGNORECASE,
    )

    if match:
        return match.group(1).strip()

    # --------------------------------------------------------
    # import math; print(<expression>)
    #
    # This is only allowed when the print body itself is a
    # plain arithmetic expression. math functions are handled
    # separately by explicit safe handlers.
    # --------------------------------------------------------

    match = re.fullmatch(
        r"\s*import\s+math\s*;\s*print\s*\(\s*([0-9\s\.\+\-\*\/\%\(\)]+)\s*\)\s*;?\s*",
        source,
        flags=re.IGNORECASE,
    )

    if match:
        return match.group(1).strip()

    return None


# ============================================================
# GENERATED PYTHON CALCULATION
# ============================================================

def _calculate_from_generated_python(
    source: str,
) -> Any:
    """
    Safely interpret deterministic Python snippets generated by
    Falcon's planner.

    Important:

    This function NEVER calls exec(), eval(), subprocess(), or
    arbitrary Python execution.

    Only explicitly recognized mathematical operations are
    supported.
    """

    source = str(
        source or ""
    ).strip()

    if not source:
        raise ValueError(
            "Python tool received empty input."
        )

    # --------------------------------------------------------
    # Factorial
    # --------------------------------------------------------

    factorial_value = (
        _extract_generated_python_factorial(
            source
        )
    )

    if factorial_value is not None:

        return math.factorial(
            factorial_value
        )

    # --------------------------------------------------------
    # Plain arithmetic inside print(...)
    # --------------------------------------------------------

    expression = (
        _extract_generated_python_expression(
            source
        )
    )

    if expression is not None:

        return _safe_eval_expression(
            expression
        )

    raise ValueError(
        "The Python tool received unsupported Python source. "
        "Only deterministic mathematical Python generated "
        "by Falcon is supported."
    )


# ============================================================
# NATURAL LANGUAGE CALCULATION
# ============================================================

def _calculate_from_question(
    question: str,
) -> Any:
    """
    Convert common natural-language mathematical questions
    into deterministic calculations.
    """

    text = str(
        question or ""
    ).strip()

    if not text:
        raise ValueError(
            "Python tool received empty input."
        )

    # --------------------------------------------------------
    # Factorial
    # --------------------------------------------------------

    factorial_value = _extract_factorial(
        text
    )

    if factorial_value is not None:

        return math.factorial(
            factorial_value
        )

    # --------------------------------------------------------
    # Percentage
    # --------------------------------------------------------

    percentage = _extract_percentage(
        text
    )

    if percentage is not None:

        percent_value, number = (
            percentage
        )

        return (
            percent_value
            / 100.0
        ) * number

    # --------------------------------------------------------
    # Strip common question wording
    # --------------------------------------------------------

    expression = text

    expression = re.sub(
        r"^\s*(what\s+is|calculate|compute|find|evaluate)\s+",
        "",
        expression,
        flags=re.IGNORECASE,
    )

    expression = re.sub(
        r"\?\s*$",
        "",
        expression,
    )

    expression = expression.strip()

    # --------------------------------------------------------
    # Convert common mathematical words
    # --------------------------------------------------------

    replacements = (
        (
            r"\bplus\b",
            "+",
        ),
        (
            r"\bminus\b",
            "-",
        ),
        (
            r"\btimes\b",
            "*",
        ),
        (
            r"\bmultiplied\s+by\b",
            "*",
        ),
        (
            r"\bdivided\s+by\b",
            "/",
        ),
        (
            r"\bover\b",
            "/",
        ),
        (
            r"\bto\s+the\s+power\s+of\b",
            "**",
        ),
        (
            r"\bpower\s+of\b",
            "**",
        ),
    )

    for pattern, replacement in replacements:

        expression = re.sub(
            pattern,
            replacement,
            expression,
            flags=re.IGNORECASE,
        )

    # --------------------------------------------------------
    # Remove harmless trailing language
    # --------------------------------------------------------

    expression = re.sub(
        r"\bplease\b",
        "",
        expression,
        flags=re.IGNORECASE,
    )

    expression = expression.strip()

    # --------------------------------------------------------
    # Mathematical expression validation
    # --------------------------------------------------------

    if not expression:

        raise ValueError(
            "No mathematical expression could be extracted."
        )

    if not re.fullmatch(
        r"[0-9\s\.\+\-\*\/\%\(\)]+",
        expression,
    ):

        raise ValueError(
            "The Python tool received a non-mathematical "
            "instruction instead of a calculation."
        )

    return _safe_eval_expression(
        expression
    )


# ============================================================
# INPUT ROUTER
# ============================================================

def _calculate(
    query: str,
) -> Any:
    """
    Determine whether the input is:

    1. Falcon-generated deterministic Python
    2. Natural-language mathematics

    and route it to the appropriate safe calculator.

    No arbitrary Python execution occurs.
    """

    text = str(
        query or ""
    ).strip()

    if not text:
        raise ValueError(
            "Python tool received empty input."
        )

    # --------------------------------------------------------
    # Generated Python
    #
    # Falcon's planner currently generates:
    #
    # import math; print(math.factorial(25))
    #
    # Detect these forms first.
    # --------------------------------------------------------

    looks_like_python = (
        "import math" in text.lower()
        or "math.factorial" in text.lower()
        or re.search(
            r"\bprint\s*\(",
            text,
            flags=re.IGNORECASE,
        )
    )

    if looks_like_python:

        return _calculate_from_generated_python(
            text
        )

    # --------------------------------------------------------
    # Natural language
    # --------------------------------------------------------

    return _calculate_from_question(
        text
    )


# ============================================================
# RESULT NORMALIZATION
# ============================================================

def _normalize_number(
    result: Any,
) -> Any:
    """
    Normalize integer-like floating-point results.
    """

    if (
        isinstance(result, float)
        and result.is_integer()
    ):
        return int(result)

    return result


# ============================================================
# PUBLIC TOOL
# ============================================================

def python_tool(
    query: str,
) -> dict:
    """
    Falcon's deterministic mathematics tool.

    Despite the historical name ``python_tool``, this layer does
    NOT execute arbitrary Python source.

    It safely supports:

        - factorial
        - percentages
        - arithmetic expressions
        - natural-language arithmetic
        - deterministic Python snippets generated by Falcon's
          planner

    All calculations are performed through explicitly allowed
    operations.
    """

    try:

        result = _calculate(
            query
        )

        result = _normalize_number(
            result
        )

        return {
            "status": "success",
            "output": result,
            "error": None,
            "metadata": {
                "mode": "deterministic_math",
            },
        }

    except Exception as exc:

        return {
            "status": "error",
            "output": None,
            "error": str(exc),
            "metadata": {
                "mode": "deterministic_math",
            },
        }