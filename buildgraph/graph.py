import functools
from collections.abc import Mapping, Sequence

from . import base_step
from .context import addToContext, getContext, makeContext
from .exception import EmptyGraphException, UnusableReturnType, pass_exceptions


class UndefinedConfig:
    pass


class Graph:
    """Graphs provide a reference to a root step and are returned by the buildgraph decorator.

    The return value of a graph can be from a step above the root step.

    Example:
              / Execute from C
    A -> B -> C
         \ But return from B
    """

    def has_single_result(self):
        """Returns true if the graph has a single return value. If it returns a tuple of steps or other
        type this returns false.
        """
        if type(self.result) == Graph or isinstance(self.result, base_step.BaseStep):
            return True
        return False

    def map_results(self, func):
        if isinstance(self.result, Mapping):
            return {r: func(self.result[r]) for r in self.result}

        if isinstance(self.result, Sequence):
            return [func(r) for r in self.result]

        raise UnusableReturnType(
            f"Graph {self.name} has unusable return type {type(self.result)}"
        )

    @staticmethod
    def assert_true(value):
        assert value

    def __init__(self, name, root, result):
        self.name = name
        self.root = root
        self.result = Graph.resolveResultToStep(result)

        if self.result is not None:
            execution_order = self.root.getExecutionOrder()
            if self.has_single_result():
                assert self.result in execution_order
            else:
                self.map_results(lambda r: self.assert_true(r in execution_order))

        addToContext(self)

    def __iter__(self):
        return iter(self.result)

    def __getitem__(self, item):
        return self.result[item]

    def __repr__(self):
        return f"<Graph {self.name}>"

    @pass_exceptions
    def run(self):
        self.root.run()
        return self.getResult()

    def getResult(self):
        """Executes and returns the result of this graph. First root.getResult() is called to execute the graph, then
        returns the return value in the appropriate format"""
        self.root.getResult()
        if self.result is None:
            return
        if self.has_single_result():
            return self.result.getResult()
        return self.map_results(lambda r: r.getResult())

    def getResultType(self):
        if self.result is None:
            return None
        return self.result.getResultType()

    @staticmethod
    def resolveResultToStep(step):
        if type(step) == Graph:
            return Graph.resolveResultToStep(step.result)
        return step

    def getFullExecution(self):
        """Gets a set of all steps and graphs that this graph depends on"""
        steps = {self}
        steps.update(self.root.getFullExecution())
        return steps

    def __getattr__(self, attr):
        return getattr(self.root, attr)


def buildgraph(outer_func=None):
    """Builds a graph from a graph-defining function and returns the last step in that graph"""

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, config=UndefinedConfig, **kwargs):
            if config == UndefinedConfig and getContext() is not None:
                config = getContext().config
            with makeContext(config) as context:
                ret = func(*args, **kwargs)

                # This can happen if no steps were defined (e.g. the graph is used to process its inputs)
                if not context.steps:
                    if not ret:
                        raise EmptyGraphException(
                            "The graph has no steps, subgraphs and return values"
                        )
                    return ret

                prev = context.steps[0]
                for step in context.steps[1:]:
                    step.after(prev)
                    prev = step

                # Pick the last defined final so that it's executed last
                root = context.steps[-1]

            return Graph(func.__name__, root, ret)

        wrapper.run = lambda *args, **kwargs: wrapper().run(*args, **kwargs)
        return wrapper

    if outer_func is None:
        return decorator

    return decorator(outer_func)
