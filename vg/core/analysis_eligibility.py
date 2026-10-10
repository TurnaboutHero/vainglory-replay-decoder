from collections.abc import Mapping, Sequence
from typing import TypedDict


POLICY_VERSION = 'vg.definitive-analysis.v1'


class AnalysisEligibility(TypedDict):
    policy_version: str
    eligible: bool
    status: str
    reason_codes: list[str]
    reason: str


def evaluate_definitive_analysis(payload: Mapping) -> AnalysisEligibility:
    """Fail closed until source-bound recording and final-result validators exist."""
    state = payload.get('player_state')
    state = state if isinstance(state, Mapping) else payload
    client = state.get('recording_client')
    client = client if isinstance(client, Mapping) else {}
    status = client.get('status')
    reasons = ['recording_source_unverified']
    if status in ('incompatible', 'mismatch', 'unsupported_version'):
        reasons.append('recording_version_mismatch')
    else:
        reasons.append('recording_version_unverified')
    reasons.append('final_result_unverified')
    return {
        'policy_version': POLICY_VERSION,
        'eligible': False,
        'status': 'excluded',
        'reason_codes': reasons,
        'reason': ('Excluded from definitive analysis: recording source/build and final result '
                   'have no source-bound verification. Layout support, supplied truth, playback '
                   'success and declared verification flags do not authorize inclusion.'),
    }


def partition_definitive_analysis(payloads: Sequence[Mapping]) -> dict:
    """Recompute admission from evidence, never from a serialized eligibility flag."""
    included = []
    excluded = []
    for payload in payloads:
        decision = evaluate_definitive_analysis(payload)
        state = payload.get('player_state')
        state = state if isinstance(state, Mapping) else {}
        if decision['eligible']:
            included.append(dict(payload))
        else:
            excluded.append({
                'input_id': payload.get('input_id'),
                'replay_file': payload.get('replay_file', payload.get('replay_path')),
                'replay_scope': payload.get('replay_scope') or state.get('replay_scope'),
                **decision,
            })
    return {'policy_version': POLICY_VERSION, 'included_matches': len(included),
            'excluded_matches': len(excluded), 'matches': included, 'excluded': excluded}
