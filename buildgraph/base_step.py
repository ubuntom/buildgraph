import inspect

from .colours import colGetter as col
from .context import addToContext
from .tabulated_writer import tabbuffer
from .timer import DurationTimer


class CircularDependencyException(Exception):
    pass


class TypeMismatchException(Exception):
    pass


class ParameterLengthException(Exception):
    pass


class BaseStep:
    """Base class for a build step.

    Subclasses should implement an `execute` method.
    """

    def __init__(self, *args):
        self.wasrun = False
        self.result = None

        self.after_deps = []
        self.bind_deps = []
        self.arg_getters = []

        self._alias = None

        addToContext(self)

        self.bind(*args)

    def alias(self, alias):
        """Sets an alias name on the step that will show when printing it.
        Useful when using multiple steps of the same type.
        """
        self._alias = alias
        return self

    def setArgGetters(self, arg_getters):
        self.arg_getters = arg_getters

    def getArgs(self):
        return [getter() for getter in self.arg_getters]

    def __repr__(self):
        msg = f"<{self.__class__.__name__}"
        if self._alias is not None:
            msg += " (" + self._alias + ")"
        msg += ">"

        return msg

    def printExecutionOrder(self):
        order = self.getExecutionOrder()

        print(f"Here's the execution order for {self}:")
        max_indent = len(str(len(order)))
        for i, step in enumerate(order):
            print(f"{i+1:^{max_indent}} {step}")
        print()

    def getExecutionOrder(self, order_list=None, downstream=None):
        """Gets the execution order of this step's dependencies.
        This function will throw an exception if a loop is detected in the dependencies.

        Args:
            order_list ([list], optional): List containing the dependencies found so far in order
            downstream ([type], optional): Downstream steps.

        Raises:
            Exception: Raised when a loop is detected

        Returns:
            [type]: [description]
        """
        if order_list is None:
            order_list = []
        if downstream is None:
            downstream = set()

        if self in order_list:
            return

        if self in downstream:
            raise CircularDependencyException(
                f"Circular dependency detected involving {self}"
            )
        downstream.add(self)

        for dep in self.after_deps:
            dep.getExecutionOrder(order_list, downstream)

        for dep in self.bind_deps:
            dep.getExecutionOrder(order_list, downstream)

        order_list.append(self)

        return order_list

    def getResult(self):
        if self.wasrun is False:
            self.callExecute()
        return self.result

    def callExecute(self):
        # Run after deps first
        for dep in self.after_deps:
            dep.getResult()

        # Get required args
        args = self.getArgs()

        print(f"Executing step {self}")
        with DurationTimer() as timer:
            with tabbuffer():
                self.result = self.execute(*args)
                self.wasrun = True

        result_text = (
            self.result
            if self.result is not None
            else f"{col.grey}{self.result}{col.clear}"
        )
        print(f"{col.green}Success{col.clear} [{timer.format()}]: {result_text}")
        print()

    def run(self):
        # Get the order so that any loops will throw
        order = self.getExecutionOrder()
        print(f"Running all {len(order)} build steps")
        print()
        with DurationTimer() as timer:
            result = self.getResult()
        print(f"Build finished in {timer.format()}")
        return result

    def after(self, *deps, front=False):
        """Add steps that this step will run after.

        e.g. b.after(a) will make b run after a

        This is for steps that aren't used by this step's execute
        method but still need to be synchronised.

        Args:
            front (bool, optional): If true, new dependencies will be inserted at the front.
                E.g. b.after(a).after(c, front=True) will run c -> a -> b
                     b.after(a).after(c) will run a -> c -> b
        """
        if front:
            self.after_deps = list(deps) + self.after_deps
        else:
            self.after_deps.extend(deps)
        return self

    def bind(self, *args):
        """Bind the arguments of the execute method. If an argument is an instance of BaseStep,
        that argument will provide its `execute` result to the execute method of this class.
        Evaluation of the `execute` method will be deferred until it is needed, and this step
        will always be run after the dependencies have run.
        """

        sig = inspect.signature(self.execute)

        print(len(sig.parameters), len(args))

        if len(sig.parameters) != len(args):
            raise ParameterLengthException(
                f"{self} expects {len(sig.parameters)} but received {len(args)}"
            )

        for param_name, arg in zip(sig.parameters, args):
            param = sig.parameters[param_name]
            arg_getter = lambda arg=arg: arg
            arg_type = type(arg)
            if issubclass(type(arg), BaseStep):
                self.bind_deps.append(arg)
                arg_getter = lambda arg=arg: arg.getResult()
                arg_type = inspect.signature(arg.execute).return_annotation

            if param.annotation != inspect._empty and arg_type != inspect._empty:
                if not issubclass(arg_type, param.annotation):
                    raise TypeMismatchException(
                        f"Setup failed. Parameter {param_name} of {self} expects {param.annotation} but got {arg_type}"
                    )

            self.arg_getters.append(arg_getter)

        return self
