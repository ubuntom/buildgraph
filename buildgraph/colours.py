COL_ON = True

COLOURS = {
    "RED": "\033[0;31m",
    "GREEN": "\033[0;32m",
    "ORANGE": "\033[0;33m",
    "GREY": "\033[1;30m",
    "CLEAR": "\033[0m",
}


def setColor(state):
    setColour(state)


def setColour(state):
    global COL_ON
    COL_ON = state


def getColour(name):
    if not COL_ON:
        return ""

    return COLOURS[name.upper()]


class ColGetter:
    def __getattr__(self, name):
        return getColour(name)


colGetter = ColGetter()
