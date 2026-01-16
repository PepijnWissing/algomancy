def solve_problem(x: int, y: int) -> int:
    """
    Solve a simple problem.

    Args:
        x: First number
        y: Second number

    Returns:
        The sum of x and y
    """
    return x + y


class Problem:
    """
    A simple problem.
    """

    def __init__(self, x: int, y: int) -> None:
        self.x = x
        self.y = y

    def solve(self) -> int:
        """
        Solve the problem by calling solve_problem

        Returns:
            The sum of members x and y
        """
        return solve_problem(self.x, self.y)
