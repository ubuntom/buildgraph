# Build Graph

Build Graph provides a set of tools to run build steps in order of their dependencies.

Build graphs can be constructed by hand, or you can let the library construct the graph for you.

In the following examples, we'll be using this step definition:
```
class Adder(BaseStep):
    """
    Returns its input added to a small random number
    """
    def execute(self, n):
        new = n + 1
        print(new)
        return new
```

## Manual construction

### Defining steps

Steps are defined by constructing a step definition and binding the required arguments.

```
# This will create a single 'Adder' step with input 5
a = Adder(5)
```

Step arguments can be other steps:

```
# This will provide the output from step a as input to step b
a = Adder(0).alias("a")  # Set an alias to identify the steps
b = Adder(a).alias("b")
```

To run the steps, we pick the last step in the graph and call its `run` method.

```
...
result = b.run()
print(result)  # 2
```

A step from anywhere in the graph can be run, but only that step's dependencies will be executed.

```
print(a.run())  # 1 - Step b won't be run
```


### Side dependencies

Sometimes you'll need to run a step `a` before step `b`, but `a`'s output won't be used by `b`.

```
class Printer(BaseStep):
    """
    Returns its input added to a small random number
    """
    def execute(self, msg):
        print(msg)

p = Printer("Hi")
a = Adder(0).alias("a")
b = Adder(a).alias("b").after(p)  # This ensures b will run after p
b.run()
```

The `after(*steps)` method specified steps that must be run first. If multiple steps are provided it doesn't enforce an ordering between those steps.


### Detatched steps

If a step is defined but not listed as a dependency it won't be run:

```
a = Adder(0).alias("a")
b = Adder(1).alias("b")
b.run()  # This won't run a
```

You can check which steps will be run with the `getExecutionOrder` and `printExecutionOrder` methods.


### Circular dependencies

Buildgraph will check for loops in the graph before running it and will raise an exception if one is detected.


## Automatic construction

The `@buildgraph` decorator builds a graph where every node is reachable from the final node.

```
@buildgraph
def addergraph():
    a = Adder(0)
    b = Adder(1)
    c = Adder(2)

addergraph.run()  # This will run all 3 steps
```

If the steps don't have dependencies the execution order isn't guaranteed, but generally the steps that are defined first will be run first unless another dependency enforces a different order.


### Returning from a graph

Graphs can return results from a step too.

```
@buildgraph
def addergraph():
    a = Adder(0)
    b = Adder(a)
    return b

result = addergraph.run() 
print(result)  # 1
```


## Extending steps

All steps must inherit from `BaseStep` and implement an `execute` method.

You can see example steps from `src/steps.py`. These steps can also be imported and used in code.


## Type checking

Buildgraph will perform type checking when the graph is built if the `execute` method has type annotations on its parameters.


## Configuring buildgraph

By default buildgraph prints coloured output. You can disable this with `buildgraph.setColor(False)`.