import asyncio
import sys


async def handle_async_reader(reader, writer):
    """Read from the asynchronous reader until EOF,
        simultaneously logging read bytes to `buffer`
        and accumulating read bytes.

    Args:
        reader: A byte reader with an async read method
        writer: A byte writer to log read bytes to

    Returns:
        bytes: All accumulated bytes read from the reader
    """
    storage = b""
    while True:
        latest = await reader.read(1024)
        if not latest:
            break
        storage += latest
        writer(latest)

    return storage


async def execute_process_and_print(command, *args, suppress_log=False, **kwargs):
    """Execute command `command` with args `args` and log stdout and stderr as they're produced.
    Also record stdout and stderr to a buffer so they can be returned.

    Args:
        command (string): The command to run
        args (List[string]): A list of args to pass to the command

    Returns:
        Tuple(int, bytes, bytes): A tuple containing exit code, stdout log and stderr log
    """
    process = await asyncio.create_subprocess_exec(
        command,
        *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        **kwargs
    )

    stdout = handle_async_reader(
        process.stdout, sys.stdout.buffer.write if not suppress_log else lambda x: None
    )
    stderr = handle_async_reader(
        process.stderr, sys.stderr.buffer.write if not suppress_log else lambda x: None
    )
    results = await asyncio.gather(process.wait(), stdout, stderr)

    return results
