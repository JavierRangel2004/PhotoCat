"""
ui_runner.py -- Subprocess runner for the PhotoCat pipeline.

Provides a generator that streams output line-by-line from the pipeline subprocess,
parses [N/M] progress tokens, and supports stop/cancel.

States: idle -> running -> (stopping | done | error)
"""

import os
import re
import signal
import subprocess
import sys
import threading
from typing import Optional

# Pattern to extract progress from log lines like "[142/274]"
_PROGRESS_RE = re.compile(r"\[(\d+)/(\d+)\]")


class PipelineRunner:
    """Manages a pipeline subprocess with streaming output."""

    def __init__(self):
        self.state: str = "idle"  # idle | running | stopping | done | error
        self.process: Optional[subprocess.Popen] = None
        self.progress: int = 0
        self.total: int = 0
        self.error_msg: str = ""
        self._lock = threading.Lock()

    def build_command(
        self,
        input_dir: str,
        csv_path: str = "",
        recursive: bool = False,
        write_xmp: bool = False,
        genre_only: bool = False,
        no_cache: bool = False,
        organize: bool = False,
        dry_run: bool = False,
        min_confidence: float = 0.55,
        workers: int = 1,
        extensions: str = ".jpg,.jpeg,.png,.tiff,.webp,.cr2,.dng",
    ) -> list[str]:
        """Build the command-line arguments for the pipeline."""
        cmd = [
            sys.executable, "-u",
            os.path.join(os.path.dirname(__file__), "main.py"),
            "--input-dir", input_dir,
        ]

        if csv_path:
            cmd += ["--csv", csv_path]
        if recursive:
            cmd += ["--recursive"]
        if write_xmp:
            cmd += ["--write-xmp"]
        if genre_only:
            cmd += ["--genre-only"]
        if no_cache:
            cmd += ["--no-cache"]
        if organize:
            cmd += ["--organize"]
        if dry_run:
            cmd += ["--dry-run"]
        if min_confidence != 0.55:
            cmd += ["--min-confidence", str(min_confidence)]
        if workers != 1:
            cmd += ["--workers", str(workers)]
        if extensions != ".jpg,.jpeg,.png,.tiff,.webp,.cr2,.dng":
            cmd += ["--extensions", extensions]

        return cmd

    def run(self, cmd: list[str]):
        """Generator that yields (line, progress_current, progress_total) tuples.

        Starts the subprocess and streams its combined stdout+stderr.
        """
        with self._lock:
            if self.state == "running":
                yield ("[ERROR] Pipeline already running.\n", 0, 0)
                return

            self.state = "running"
            self.progress = 0
            self.total = 0
            self.error_msg = ""

        try:
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                cwd=os.path.dirname(__file__),
                # On Windows, CREATE_NEW_PROCESS_GROUP allows sending CTRL_BREAK
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0,
            )
        except Exception as e:
            self.state = "error"
            self.error_msg = str(e)
            yield (f"[ERROR] Failed to start pipeline: {e}\n", 0, 0)
            return

        for line in self.process.stdout:
            # Parse progress
            m = _PROGRESS_RE.search(line)
            if m:
                self.progress = int(m.group(1))
                self.total = int(m.group(2))

            yield (line, self.progress, self.total)

            # Check if stop was requested
            if self.state == "stopping":
                break

        # Wait for process to finish
        retcode = self.process.wait()
        self.process = None

        if self.state == "stopping":
            self.state = "idle"
            yield ("\n[STOPPED] Pipeline stopped by user.\n", self.progress, self.total)
        elif retcode == 0:
            self.state = "done"
            yield ("\n[DONE] Pipeline completed successfully.\n", self.progress, self.total)
        else:
            self.state = "error"
            self.error_msg = f"Exit code {retcode}"
            yield (f"\n[ERROR] Pipeline exited with code {retcode}.\n", self.progress, self.total)

    def stop(self) -> str:
        """Request the running pipeline to stop."""
        if self.state != "running" or self.process is None:
            return "No pipeline running."

        self.state = "stopping"
        try:
            if sys.platform == "win32":
                self.process.terminate()
            else:
                self.process.send_signal(signal.SIGTERM)
            return "Stop signal sent."
        except Exception as e:
            return f"Error stopping: {e}"

    def is_running(self) -> bool:
        return self.state == "running"

    def get_status(self) -> str:
        if self.state == "idle":
            return "Ready"
        elif self.state == "running":
            if self.total > 0:
                return f"Running: {self.progress}/{self.total}"
            return "Running..."
        elif self.state == "stopping":
            return "Stopping..."
        elif self.state == "done":
            return f"Done ({self.total} images)"
        elif self.state == "error":
            return f"Error: {self.error_msg}"
        return self.state

    def get_progress_fraction(self) -> float:
        """Return 0.0 to 1.0 progress."""
        if self.total > 0:
            return min(self.progress / self.total, 1.0)
        return 0.0
