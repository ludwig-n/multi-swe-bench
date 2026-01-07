# Copyright (c) 2024 Bytedance Ltd. and/or its affiliates

#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at

#      http://www.apache.org/licenses/LICENSE-2.0

#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

import logging
from pathlib import Path
import threading
import time
import subprocess
from typing import Optional, Union


def exists(image_name: str) -> bool:
    return True


def build(
    workdir: Path, dockerfile_name: str, image_full_name: str, logger: logging.Logger
):
    pass


def run(
    image_full_name: str,
    run_command: str,
    output_path: Optional[Path] = None,
    global_env: Optional[list[str]] = None,
    volumes: Optional[Union[dict[str, str], list[str]]] = None,
) -> str:
    assert not global_env, "global_env is not supported for now"
    assert not volumes, "volumes are not supported for now"

    output, _, _ = exec_run_with_timeout(run_command, timeout=None)

    if output_path is not None:
        output_path.write_text(output)

    return output


# Copied from https://github.com/Kipok/SWE-bench/blob/0f341d38df5ca749c74eff61b06033a2c9b2793e/swebench/harness/run_local_evaluation.py#L73
# In the original Multi-SWE-bench code, there was no timeout for Docker commands, so we don't use it either.
def exec_run_with_timeout(cmd, timeout: int | None = None):
    """
    Run a command locally with a timeout.

    Args:
        cmd (str): Command to run.
        timeout (int): Timeout in seconds.
    """
    # Local variables to store the result of executing the command
    exec_result = b""
    process = None
    exception = None
    timed_out = False

    # Wrapper function to run the command
    def run_command():
        nonlocal exec_result, process, exception
        try:
            process = subprocess.Popen(
                cmd,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=False
            )
            exec_result, _ = process.communicate()
        except Exception as e:
            exception = e

    # Start the command in a separate thread
    thread = threading.Thread(target=run_command)
    start_time = time.time()
    thread.start()
    thread.join(timeout)

    if exception:
        raise exception

    # If the thread is still alive, the command timed out
    if thread.is_alive():
        if process is not None:
            try:
                process.terminate()
                # Give it a moment to terminate gracefully
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
        timed_out = True
    end_time = time.time()
    return exec_result.decode(), timed_out, end_time - start_time
