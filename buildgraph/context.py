from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Context:
    steps: list = field(default_factory=list)
    config: Optional[dict] = None


CONTEXTS = []


@contextmanager
def makeContext(config=None):
    global CONTEXTS

    CONTEXTS.append(Context())
    CONTEXTS[-1].config = config

    yield CONTEXTS[-1]

    CONTEXTS.pop()


def addToContext(instance):
    """Add a build step to the current context"""
    if not CONTEXTS:
        return
    CONTEXTS[-1].steps.append(instance)


def getContext():
    if not CONTEXTS:
        return
    return CONTEXTS[-1]


def setConfig(config):
    global CONFIG
    CONFIG = config
