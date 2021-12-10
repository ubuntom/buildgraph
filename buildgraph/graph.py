import functools

from buildgraph.base_step import BaseStep

from .context import getContext, makeContext
from .steps import ResultAggregatingStep, StepSyncingStep


class Graph:
    def __init__(self, root, result):
        self.root = root
        self.result = result

    def run(self):
        self.root.run()
        if self.result:
            return self.result.getResult()

    def __getattr__(self, attr):
        return getattr(self.root, attr)


def buildgraph():
    """Builds a graph from a graph-defining function and returns the last step in that graph"""

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, config=None, **kwargs):
            with makeContext(config) as context:
                ret = func(*args, **kwargs)

                non_finals = set()
                for step in context.steps:
                    above = step.getExecutionOrder()[:-1]
                    non_finals.update(above)

                finals = [step for step in context.steps if step not in non_finals]

                root = finals[-1]
                for step in finals[:-1]:
                    root.after(step)

                return Graph(root, ret)

        return wrapper

    return decorator
