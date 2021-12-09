CONTEXT = None


def addToContext(instance):
    if CONTEXT is None:
        return
    CONTEXT.append(instance)
