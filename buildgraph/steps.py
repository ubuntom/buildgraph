import asyncio
from dataclasses import dataclass

from .base_step import BaseStep
from .utils import execute_process_and_print


class CommandStep(BaseStep):
    """Run a command and return the result of it as well as stdout and stderr logs.

    Raises:
        CommandStep.UnexpectedReturnCode: If the return code doesn't match the provided one

    Returns:
        CommandStep.Result object containing the return code, stdout and stderr
    """

    @dataclass
    class Result:
        code: int
        stdout: bytes
        stderr: bytes

        def __repr__(self):
            return f"CommandStep.Result(code={self.code})"

    class UnexpectedReturnCode(Exception):
        pass

    def execute(self, command, *args, expected_code=0, suppress_log=False, **kwargs):
        loop = asyncio.get_event_loop()

        output = loop.run_until_complete(
            execute_process_and_print(
                command, *args, suppress_log=suppress_log, **kwargs
            )
        )
        results = CommandStep.Result(output[0], output[1], output[2])

        if expected_code is not None and results.code != expected_code:
            raise CommandStep.UnexpectedReturnCode(
                f"Command returned {results.code} but expected {expected_code}"
            )

        return results
