from collections.abc import Sequence
from typing import Literal, TypedDict


class InputResult(TypedDict):
    input_id: str
    replay_file: str
    status: Literal['complete', 'failed']
    error_code: str | None
    error: str | None


class BatchReport(TypedDict):
    status: Literal['complete', 'partial', 'failed', 'empty']
    discovered: int
    succeeded: int
    failed: int
    results: list[InputResult]


class PartialBatchError(ValueError):
    def __init__(self, report: BatchReport):
        self.report = report
        super().__init__(f'{report["failed"]} of {report["discovered"]} replay inputs failed')


def batch_report(results: Sequence[InputResult]) -> BatchReport:
    """Account for every discovered input; callers count success only after publication."""
    failed = sum(row['status'] == 'failed' for row in results)
    succeeded = len(results) - failed
    status = 'empty' if not results else 'failed' if not succeeded else 'partial' if failed else 'complete'
    return {'status': status, 'discovered': len(results), 'succeeded': succeeded,
            'failed': failed, 'results': list(results)}
