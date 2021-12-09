import functools

from .context import getContext, makeContext
from .steps import ResultAggregatingStep, StepSyncingStep


def buildgraph():
    """Builds a graph from a graph-defining function and returns the last step in that graph
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, config=None, **kwargs):
            with makeContext(config) as context:
                last = func(*args, **kwargs)

                if last is None:
                    print(
                        "Graph building function didn't return a step, so the last defined step will be the final step"
                    )
                    base = StepSyncingStep()

                else:
                    base = ResultAggregatingStep(last)

                order = base.getExecutionOrder()
                for step in context.steps[-1::-1]:
                    if step not in order:
                        base.after(step, front=True)
                        order = base.getExecutionOrder()

                return base

        return wrapper

    return decorator
