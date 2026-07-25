import asyncio
import logging

logger = logging.getLogger(__name__)


class ConversionError(Exception):
    pass


async def run_subprocess(*args: str, timeout: float = 600) -> None:
    """Shared subprocess runner for all converters — consistent logging/error handling."""
    logger.info("Running: %s", " ".join(args))
    proc = await asyncio.create_subprocess_exec(
        *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
    except asyncio.TimeoutError:
        proc.kill()
        raise ConversionError(f"Process timed out after {timeout}s: {args[0]}")

    if proc.returncode != 0:
        raise ConversionError(
            f"{args[0]} failed (exit {proc.returncode}): {stderr.decode(errors='replace')[-2000:]}"
        )
