from buildgraph import BaseStep, buildgraph


class AppendAndPrint(BaseStep):
    def configure(self, config):
        self.namespace = config["namespace"]

    def execute(self, string):
        string = self.namespace + "(" + string + ")"
        print(string)
        return string


@buildgraph()
def getInnerGraph(p):
    print(f"Building inner graph with input {p}")
    return AppendAndPrint(p)


@buildgraph()
def getProxyGraph(g):
    print(f"Building proxy graph with input {g}")
    return getInnerGraph(g, config={"namespace": "proxy"})


@buildgraph()
def getOuterGraph(p):
    print(f"Building outer graph with input {p}")
    inner1 = getInnerGraph(p, config={"namespace": "inner1"})
    inner2 = getInnerGraph(inner1, config={"namespace": "inner2"})
    proxy = getProxyGraph(inner2)
    outer = AppendAndPrint(proxy)
    return outer


if __name__ == "__main__":
    graph = getOuterGraph("Hello", config={"namespace": "outer"})
    print()
    graph.printExecutionOrder()
    graph.run()
