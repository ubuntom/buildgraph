import inspect

from . import base_step, graph


class TypeMismatchException(Exception):
    pass


class ParameterLengthException(Exception):
    pass


class Binding:
    def __init__(self, *args, **kwargs):
        self.args = list(args)  # Convert to list so it's mutable
        self.kwargs = kwargs

        self.bind_deps = []
        self.arg_getters = []
        self.kwarg_getters = {}

    def resolve_arg(self, param, arg):
        """Resolves the argument to a step's execute function and returns a
        function that will return the true value of the argument.

        For arguments that are themselves steps, the function will return the
        resul of the step.

        For all other arguments, the function will return the value of the argument.
        """

        getter = lambda arg=arg: arg
        arg_type = type(arg)
        if issubclass(type(arg), base_step.BaseStep) or type(arg) == graph.Graph:
            self.bind_deps.append(arg)
            getter = lambda arg=arg: arg.getResult()
            arg_type = arg.getResultType()

        if param.annotation != inspect._empty and arg_type != inspect._empty:
            if not issubclass(arg_type, param.annotation):
                raise TypeMismatchException(
                    f"Setup failed. Parameter {param.name} of {self} expects {param.annotation} but got {arg_type}"
                )

        return getter

    def bind_arg(self, param):
        """Attempt to fulfill the param with a positional argument

        Returns:
            bool: True if the argument could be bound
        """
        if not self.args:
            return False
        arg = self.args.pop(0)
        getter = self.resolve_arg(param, arg)
        self.arg_getters.append(getter)
        return True

    def bind_kwarg(self, param):
        """Attempt to fulfill the param with a keyword argument

        Returns:
            bool: True if the argument could be bound
        """
        if param.name not in self.kwargs:
            return False
        kwarg = self.kwargs[param.name]
        del self.kwargs[param.name]
        getter = self.resolve_arg(param, kwarg)
        self.kwarg_getters[param.name] = getter
        return True

    def bind_all_kwargs(self, param):
        """Fulfill the variadic param with all keyword arguments.
        This is used for variadic keyword arguments
        """
        while self.kwargs:
            first = next(iter(self.kwargs.keys()))
            kwarg = self.kwargs[first]
            del self.kwargs[first]
            getter = self.resolve_arg(param, kwarg)
            self.kwarg_getters[first] = getter

    def consume_arg(self, param: inspect.Parameter, use_arg: bool, use_kwarg: bool):
        """Consumes an argument from the args list or kwargs dict to
        satisfy the parameter.

        If an argument can't be found and the param doesn't have a default
        value an exception will be thrown.

        Params:
            param: The pramater to bind an argument to
            use_arg: Whether to use positional args for binding
            use_kwarg: Whether to use keyword args for binding
        """
        optional = param.default != inspect._empty

        bound = False
        if use_arg:  # Try binding with a positional arg
            bound = self.bind_arg(param)

        if not bound and use_kwarg:  # Try with a keyword arg
            bound = self.bind_kwarg(param)

        if not bound and not optional:
            # If we couldn't bind an arg or a kwarg and the param has no default, raise an exception
            raise ParameterLengthException(
                f"{self} expected an argument for parameter {param.name}"
            )

    def evaluateArgs(self):
        return (
            [getter() for getter in self.arg_getters],
            {k: getter() for k, getter in self.kwarg_getters.items()},
        )

    def bind(self, function):
        """Bind the arguments to the provided signature. If an argument is an instance of BaseStep,
        that argument will provide its result to the as the bound value and evaluation of the step
        will be deferred until it is needed.

        Returns structures containing functions that will return the value of each argument.
        """

        signature = inspect.signature(function)

        for param in signature.parameters.values():
            # There are 5 kinds of parameter that have different cases:
            if param.kind == param.POSITIONAL_ONLY:
                # Consume one arg
                self.consume_arg(param, True, False)
            elif param.kind == param.VAR_POSITIONAL:
                # Consume all args
                while self.args:
                    self.bind_arg(param)
            elif param.kind == param.POSITIONAL_OR_KEYWORD:
                # Try an arg, otherwise a kwarg
                self.consume_arg(param, True, True)
            elif param.kind == param.KEYWORD_ONLY:
                # Consume one kwarg
                self.consume_arg(param, False, True)
            elif param.kind == param.VAR_KEYWORD:
                # Consume all kwargs
                self.bind_all_kwargs(param)

        # If there are any left over arguments raise an exception
        if self.args:
            raise ParameterLengthException(
                f"{self} received {len(self.args)} unexpected arguments"
            )
        if self.kwargs:
            raise ParameterLengthException(
                f"{self} received unexpected keyword arguments: {[k for k in self.kwargs.keys()]}"
            )

        return self
