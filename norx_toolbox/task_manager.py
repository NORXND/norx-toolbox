import asyncio
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Callable, Awaitable, Any
from uuid import uuid4

if TYPE_CHECKING:
    from aiogram import Bot
    from quart import Quart

logger = logging.getLogger(__name__)


class TaskKind(str, Enum):
    DOWNLOAD = "download"
    CONVERT = "convert"
    TRIM = "trim"


class JobStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"


@dataclass
class Job:
    id: str
    user_id: int
    kind: TaskKind
    status: JobStatus = JobStatus.QUEUED
    error: str | None = None
    task: asyncio.Task | None = field(default=None, repr=False)


class TaskManager:
    _sems: dict[TaskKind, asyncio.Semaphore]
    _user_sems: dict[int, asyncio.Semaphore]
    jobs: dict[str, Job]

    bot: 'Bot'
    web_server: 'Quart'

    def __init__(self, bot, web_server):
        self.bot = bot
        self.web_server = web_server
        
        # Separate pools: downloads limited by remote-host risk, conversions by local CPU
        self._sems = {
            TaskKind.DOWNLOAD: asyncio.Semaphore(3),
            TaskKind.CONVERT: asyncio.Semaphore(2),
            TaskKind.TRIM: asyncio.Semaphore(2),
        }
        self._user_sems = {}
        self._user_sem_limit = 10  # 10 concurrent job per user, across all kinds

        self.jobs = {}

    def _user_sem(self, user_id: int) -> asyncio.Semaphore:
        if user_id not in self._user_sems:
            self._user_sems[user_id] = asyncio.Semaphore(self._user_sem_limit)
        return self._user_sems[user_id]

    def submit(
        self,
        user_id: int,
        kind: TaskKind,
        coro_fn: Callable[[], Awaitable[Any]],
        on_done: Callable[[Job, Any], Awaitable[None]] | None = None,
        on_error: Callable[[Job, Exception], Awaitable[None]] | None = None,
    ) -> Job:
        job = Job(id=uuid4().hex[:8], user_id=user_id, kind=kind)
        self.jobs[job.id] = job

        job.task = asyncio.create_task(
            self._run(job, coro_fn, on_done, on_error),
            name=f"{kind.value}:{job.id}",
        )
        return job

    async def _run(self, job: Job, coro_fn, on_done, on_error):
        kind_sem = self._sems[job.kind]
        user_sem = self._user_sem(job.user_id)

        async with user_sem:
            async with kind_sem:
                job.status = JobStatus.RUNNING
                try:
                    result = await coro_fn()
                    job.status = JobStatus.DONE
                    if on_done:
                        await on_done(job, result)
                except Exception as e:
                    job.status = JobStatus.FAILED
                    job.error = str(e)
                    logger.exception("Job %s failed", job.id)
                    if on_error:
                        await on_error(job, e)
                finally:
                    # keep finished jobs around briefly for /status, then drop
                    asyncio.get_event_loop().call_later(300, self.jobs.pop, job.id, None)

    def queue_position(self, kind: TaskKind) -> int:
        """Rough count of jobs of this kind currently queued/running - for user feedback."""
        return sum(1 for j in self.jobs.values() if j.kind == kind and j.status in (JobStatus.QUEUED, JobStatus.RUNNING))

    def user_active_jobs(self, user_id: int) -> list[Job]:
        return [j for j in self.jobs.values() if j.user_id == user_id and j.status in (JobStatus.QUEUED, JobStatus.RUNNING)]