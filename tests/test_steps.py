from dataclasses import dataclass

import pytest

from buildgraph import (
    BaseStep,
    CircularDependencyException,
    ParameterLengthException,
    TypeMismatchException,
    buildgraph,
)
from buildgraph.base_step import StepFailedException
from buildgraph.graph import EmptyGraphException


class ReturnStep(BaseStep):
    def execute(self, v):
        return v


class RunStep(BaseStep):
    def execute(self, func):
        func()


class AddStep(BaseStep):
    def execute(self, a, b):
        return a + b


class ConfigStep(BaseStep):
    def configure(self, config):
        self.name = config["name"]

    def execute(self):
        return f"My name is {self.name}"


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
    @buildgraph()
    def getTest():
        ReturnStep(None).alias("A")
        b = ReturnStep(4).alias("B")
        return ReturnStep(b).alias("C")

    test = getTest()
    order = test.getExecutionOrder()
    assert len(order) == 3
    assert order[0]._alias == "A"
    assert order[-1]._alias == "C"

    assert test.run() == 4


def test_graph_builder_no_ret():
    @buildgraph()
    def getTest():
        ReturnStep(4)

    test = getTest()
    assert test.run() is None


def test_graph_builder_ret_out_of_order():
    @buildgraph()
    def getTest():
        a = ReturnStep(4).alias("a")
        ReturnStep(5).alias("b")
        return a

    test = getTest()
    order = test.getExecutionOrder()
    assert order[0]._alias == "a"
    assert order[1]._alias == "b"
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


def test_param_graph():
    @buildgraph()
    def loopinggraph(loops):
        a = AddStep(0, 1)
        for i in range(loops - 1):
            a = AddStep(a, 1)
        return a

    looponce = loopinggraph(1)
    assert looponce.run() == 1

    loopmany = loopinggraph(5)
    assert loopmany.run() == 5


def test_config_graph():
    @buildgraph()
    def getConfiggraph():
        return ConfigStep()

    graph = getConfiggraph(config={"name": "bob"})

    assert graph.run() == "My name is bob"


def test_nested_steps():
    def moreSteps(a, b):
        return AddStep(a, b)

    @buildgraph()
    def getGraph(n):
        a = AddStep(1, 0)
        return moreSteps(a, n)

    graph = getGraph(2)

    assert graph.run() == 3


def test_sub_graph():
    @buildgraph()
    def getSubgraph(a, b):
        return AddStep(a, b)

    @buildgraph()
    def getMainGraph(n):
        s = ReturnStep(2)
        subgraph = getSubgraph(n, s)
        return AddStep(subgraph, 3)

    assert getMainGraph(1).run() == 6


def test_exception():
    class StepException(Exception):
        pass

    class ExceptionStep(BaseStep):
        def execute(self, a):
            raise StepException(str(a))

    @buildgraph()
    def getGraph():
        ExceptionStep(0)
        ExceptionStep(1)

    with pytest.raises(StepFailedException) as einfo:
        g = getGraph().run()

    e = einfo.value

    assert type(e.exc) == StepException
    assert e.args == (0,)
    assert str(e.step) == "<ExceptionStep>"


def test_empty_graph():
    @buildgraph()
    def getGraph():
        pass

    with pytest.raises(EmptyGraphException):
        getGraph()
