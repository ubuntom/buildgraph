import functools

from .context import addToContext, getContext, makeContext


class UndefinedConfig:
    pass


class EmptyGraphException(Exception):
    pass


class Graph:
    """Graphs provide a reference to a root step and are returned by the buildgraph decorator.

    The return value of a graph can be from a step above the root step.

    Example:
              / Execute from C
    A -> B -> C
         \ But return from B
    """

    def __init__(self, name, root, result):
        self.name = name
        self.root = root
        self.result = Graph.resolveResultToStep(result)

        if result is not None:
            assert self.result in self.root.getExecutionOrder()

        addToContext(self)

    def __repr__(self):
        return f"<Graph {self.name}>"

    def run(self):
        self.root.run()
        return self.getResult()

    def getResult(self):
        self.root.getResult()
        if self.result is not None:
            return self.result.getResult()

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


def buildgraph():
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

    return decorator
