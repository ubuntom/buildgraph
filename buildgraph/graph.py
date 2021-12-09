from . import context
from .steps import ResultAggregatingStep, StepSyncingStep


def buildgraph(func):
    global CONTEXT
    context.CONTEXT = []

    last = func()

    print(context.CONTEXT)

    if last is None:
        print(
            "Graph building function didn't return a step, so the last defined step will be the final step"
        )
        base = StepSyncingStep()

    else:
        base = ResultAggregatingStep(last)

    order = base.getExecutionOrder()
    for step in context.CONTEXT[-1::-1]:
        if step not in order:
            base.after(step, front=True)
            order = base.getExecutionOrder()

    return base
