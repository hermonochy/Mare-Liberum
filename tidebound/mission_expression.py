import ast
import operator


_BINARY_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
}
_COMPARE_OPERATORS = {
    ast.Eq: operator.eq,
    ast.NotEq: operator.ne,
    ast.Lt: operator.lt,
    ast.LtE: operator.le,
    ast.Gt: operator.gt,
    ast.GtE: operator.ge,
    ast.In: lambda left, right: left in right,
    ast.NotIn: lambda left, right: left not in right,
}


class MissionExpressionError(ValueError):
    pass


class MissionExpression:
    def __init__(self, expression):
        self.expression = str(expression or "").strip()
        if not self.expression:
            self.tree = ast.parse("True", mode="eval")
        else:
            try:
                self.tree = ast.parse(self.expression, mode="eval")
            except SyntaxError as error:
                raise MissionExpressionError(f"Invalid mission expression: {error.msg}") from error
        self._validate(self.tree)

    def _validate(self, node):
        allowed = (
            ast.Expression, ast.Constant, ast.Name, ast.BoolOp, ast.And, ast.Or,
            ast.UnaryOp, ast.Not, ast.USub, ast.UAdd, ast.BinOp, ast.Compare,
            ast.Call, ast.Load, ast.Add, ast.Sub, ast.Mult, ast.Div, ast.FloorDiv,
            ast.Mod, ast.Eq, ast.NotEq, ast.Lt, ast.LtE, ast.Gt, ast.GtE,
            ast.In, ast.NotIn,
        )
        if not isinstance(node, allowed):
            raise MissionExpressionError(f"Unsupported expression element: {type(node).__name__}")
        if isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name) or node.keywords:
                raise MissionExpressionError("Only named mission functions with positional arguments are allowed")
        for child in ast.iter_child_nodes(node):
            self._validate(child)

    def evaluate(self, variables=None, functions=None):
        variables = variables or {}
        functions = functions or {}
        return self._evaluate(self.tree.body, variables, functions)

    def _evaluate(self, node, variables, functions):
        if isinstance(node, ast.Constant):
            return node.value
        if isinstance(node, ast.Name):
            key = node.id.lower()
            if key in {"true", "false"}:
                return key == "true"
            if key not in variables:
                raise MissionExpressionError(f"Unknown mission variable '{node.id}'")
            value = variables[key]
            return value() if callable(value) else value
        if isinstance(node, ast.BoolOp):
            if isinstance(node.op, ast.And):
                return all(self._evaluate(value, variables, functions) for value in node.values)
            return any(self._evaluate(value, variables, functions) for value in node.values)
        if isinstance(node, ast.UnaryOp):
            value = self._evaluate(node.operand, variables, functions)
            if isinstance(node.op, ast.Not):
                return not value
            if isinstance(node.op, ast.USub):
                return -value
            if isinstance(node.op, ast.UAdd):
                return +value
        if isinstance(node, ast.BinOp):
            left = self._evaluate(node.left, variables, functions)
            right = self._evaluate(node.right, variables, functions)
            operation = _BINARY_OPERATORS.get(type(node.op))
            if operation is None:
                raise MissionExpressionError("Unsupported arithmetic operator")
            try:
                return operation(left, right)
            except (ArithmeticError, TypeError) as error:
                raise MissionExpressionError(f"Invalid arithmetic in mission expression: {error}") from error
        if isinstance(node, ast.Compare):
            left = self._evaluate(node.left, variables, functions)
            for operation_node, comparator in zip(node.ops, node.comparators):
                right = self._evaluate(comparator, variables, functions)
                operation = _COMPARE_OPERATORS.get(type(operation_node))
                if operation is None:
                    raise MissionExpressionError("Unsupported comparison operator")
                try:
                    if not operation(left, right):
                        return False
                except (TypeError, ValueError):
                    return False
                left = right
            return True
        if isinstance(node, ast.Call):
            name = node.func.id.lower()
            function = functions.get(name)
            if function is None:
                raise MissionExpressionError(f"Unknown mission function '{name}'")
            arguments = [self._evaluate(argument, variables, functions) for argument in node.args]
            try:
                return function(*arguments)
            except TypeError as error:
                raise MissionExpressionError(f"Invalid arguments for mission function '{name}': {error}") from error
        raise MissionExpressionError(f"Unsupported expression element: {type(node).__name__}")


def legacy_condition_to_expression(lines):
    def leaf(text):
        value = text.strip()
        lowered = value.lower()
        if lowered in {"never", "always"}:
            return "false" if lowered == "never" else "true"
        if lowered.startswith("expression "):
            return value.split(None, 1)[1].strip().strip("\"'")
        if lowered.startswith("has ") or lowered.startswith("not "):
            negate = lowered.startswith("not ")
            payload = value.split(None, 1)[1].strip()
            if len(payload) >= 2 and payload[0] == payload[-1] and payload[0] in {"\"", "'"}:
                payload = payload[1:-1]
            state = None
            for suffix in (": done", ": active", ": offered", ": failed", ": available"):
                if payload.lower().endswith(suffix):
                    payload = payload[:-len(suffix)].strip()
                    state = suffix[2:]
                    break
            if state is not None:
                return f"mission({payload!r}) { '!=' if negate else '==' } {state!r}"
            return f"flag({payload!r}) == {'false' if negate else 'true'}"
        if lowered.startswith("distance "):
            import re
            match = re.match(r'distance\s+([\"\'])(.*?)\1\s*(>=|<=|==|!=|>|<)\s*(-?\d+(?:\.\d+)?)$', value, re.IGNORECASE)
            if match:
                port, operator_text, amount = match.group(2), match.group(3), match.group(4)
                return f"distance_to_port({port!r}) {operator_text} {amount}"
        if lowered.startswith("random "):
            return value
        return ""

    def parse_block(items, start, indent):
        expressions = []
        operators = []
        index = start
        while index < len(items):
            current_indent, text = items[index]
            if current_indent < indent:
                break
            if current_indent > indent:
                nested, index = parse_block(items, index, current_indent)
                if nested:
                    expressions.append(nested)
                continue
            lowered = text.lower()
            if lowered in {"and", "or"}:
                operator_text = lowered
                index += 1
                if index < len(items) and items[index][0] > indent:
                    nested, index = parse_block(items, index, items[index][0])
                    if nested:
                        if expressions:
                            operators.append(operator_text)
                        expressions.append(f"({nested})")
                else:
                    operators.append(operator_text)
                continue
            expression = leaf(text)
            index += 1
            if expression:
                if expressions and len(operators) < len(expressions):
                    operators.append("and")
                expressions.append(f"({expression})")
            if index < len(items) and items[index][0] > indent:
                nested, index = parse_block(items, index, items[index][0])
                if nested:
                    if expressions and len(operators) < len(expressions):
                        operators.append("and")
                    expressions.append(f"({nested})")
        if not expressions:
            return "", index
        result = expressions[0]
        for operator_text, expression in zip(operators, expressions[1:]):
            result = f"{result} {operator_text} {expression}"
        return result, index

    if not lines:
        return ""
    first_indent = min(indent for indent, _ in lines)
    expression, _ = parse_block(lines, 0, first_indent)
    return expression

