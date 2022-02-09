from buildgraph import BaseStep, buildgraph

import inspect
print(inspect.getfile(BaseStep))


class RunTest(BaseStep):
    def configure(self, config):
        self.root = config['code_root']

    def execute(self, subDir, skip_integration=False):
        config = ""
        if skip_integration:
            config = " Skipping integration tests"
        print(f"Testing {self.root}/{subDir}/{config}")
        # Test code here

class BuildPackage(BaseStep):
    def execute(self, prod):
        mode = "production" if prod else "development"
        print(f"Building {mode} package")
        # Packaging code here
        package = f"builtpackage-{mode}"
        return package

class UploadPackage(BaseStep):
    def execute(self, package):
        print(f"Uploading package {package}")
        # Upload code here

class WritePackageToFile(BaseStep):
    def execute(self, package, destination):
        print(f"Copying package {package} to {destination}")
        # Copying code here

@buildgraph()
def getGraph(prod=True):
    RunTest("api")
    RunTest("client", skip_integration=True)
    package = BuildPackage(prod)
    if prod:
        UploadPackage(package)
    else:
        WritePackageToFile(package, "packages/")


if __name__ == "__main__":
    test_graph = getGraph(False, config={"code_root": "src"})
    test_graph.printExecutionOrder()
    test_graph.run()

    prod_graph = getGraph(True, config={"code_root": "src"})
    prod_graph.printExecutionOrder()
    prod_graph.run()
