import inspect
import traceback

from .binding import Binding
from .colours import colGetter as col
from .context import addToContext, getContext
from .exception import CircularDependencyException, StepFailedException, pass_exceptions
from .graph import Graph
from .tabulated_writer import tabbuffer
from .timer import DurationTimer


class BaseStep:
    """Base class for a build step.

    Subclasses should implement an `execute` method.
    """

    def __init__(self, *args, indent_log=False, **kwargs):
        self.config = None

        self.indent_log = indent_log

        self.wasrun = False
        self.result = None

        self.after_deps = []

        self._alias = None

        addToContext(self)

        context = getContext()
        if context is not None:
            self.configure(context.config)

        self.binding = Binding(*args, **kwargs).bind(self.execute)

    def configure(self, config):
        pass

    def alias(self, alias):
        """Sets an alias name on the step that will show when printing it.
        Useful when using multiple steps of the same type.
        """
        self._alias = alias
        return self

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

        for dep in self.binding.bind_deps:
            dep.getExecutionOrder(order_list, downstream)

        order_list.append(self)

        return order_list

    def getFullExecution(self):
        steps = {self}
        for step in self.after_deps:
            steps.update(step.getFullExecution())
        for step in self.binding.bind_deps:
            steps.update(step.getFullExecution())
        return steps

    def getResult(self):
        if self.wasrun is False:
            self.callExecute()
        return self.result

    def getResultType(self):
        return inspect.signature(self.execute).return_annotation

    def callExecute(self):
        # Run after deps first
        for dep in self.after_deps:
            dep.getResult()

        for dep in self.binding.bind_deps:
            dep.getResult()

        # Get required args
        args, kwargs = self.binding.evaluateArgs()

        print(f"{col.orange}Executing step {self}{col.clear}")
        with DurationTimer() as timer:
            try:
                with tabbuffer(self.indent_log):
                    self.result = self.execute(*args, **kwargs)
                    self.wasrun = True
            except Exception as e:
                with tabbuffer():
                    print(traceback.format_exc())
                print(f"{col.red}Failed{col.clear}")
                raise StepFailedException(self, e, args) from None

        result_text = (
            self.result
            if self.result is not None
            else f"{col.grey}{self.result}{col.clear}"
        )
        print(f"{col.green}Success{col.clear} [{timer.format()}]: {result_text}")
        print()

    @pass_exceptions
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
