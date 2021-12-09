import pytest

from buildgraph import (
    BaseStep,
    CircularDependencyException,
    ParameterLengthException,
    TypeMismatchException,
    buildgraph,
)


class ReturnStep(BaseStep):
    def execute(self, v):
        return v


class RunStep(BaseStep):
    def execute(self, func):
        func()


class AddStep(BaseStep):
    def execute(self, a, b):
        return a + b


class NeedsIntStep(BaseStep):
    def execute(self, a: int) -> int:
        return a


class ReturnsStringStep(BaseStep):
    def execute(self) -> str:
        return "no"


class Counter:
    def __init__(self) -> None:
        self.i = 0

    def __call__(self) -> None:
        self.i += 1


def test_returns_input():
    step = ReturnStep(5)
    assert step.run() == 5


def test_returns_input_from_step():
    a = ReturnStep(5)
    step = ReturnStep(a)
    assert step.run() == 5


def test_runs_once():
    c = Counter()
    a = RunStep(c)
    a.run()
    a.run()

    assert c.i == 1


def test_downstream_not_run():
    c = Counter()

    a = RunStep(c)
    b = RunStep(c).after(a)
    a.run()

    assert c.i == 1

    b.run()
    assert c.i == 2


def test_circular_dependency():
    a = ReturnStep(0)
    b = ReturnStep(a)
    a.after(b)
    with pytest.raises(CircularDependencyException):
        a.run()


def test_two_dependencies():
    assert AddStep(1, 2).run() == 3


def test_after_dependencies():
    c = Counter()

    a = RunStep(lambda: [c() for _ in range(c.i)])
    b = RunStep(c).after(a)

    b.run()

    assert c.i == 1
    assert a.wasrun is True


def test_graph_builder():
    @buildgraph
    def test():
        ReturnStep(None).alias("A")
        b = ReturnStep(4).alias("B")
        return ReturnStep(b).alias("C")

    order = test.getExecutionOrder()
    assert len(order) == 4
    assert order[0]._alias == "A"
    assert order[-2]._alias == "C"

    assert test.run() == 4


def test_const_type_match():
    NeedsIntStep(5)


def test_const_type_mismatch():
    with pytest.raises(TypeMismatchException):
        NeedsIntStep("no")


def test_returned_type_match():
    a = NeedsIntStep(5)
    NeedsIntStep(a)


def test_returned_type_mismatch():
    a = ReturnsStringStep()
    with pytest.raises(TypeMismatchException):
        NeedsIntStep(a)


def test_type_length_mismatch_long():
    with pytest.raises(ParameterLengthException):
        NeedsIntStep(1, 2)


def test_type_length_mismatch_short():
    with pytest.raises(ParameterLengthException):
        NeedsIntStep()
