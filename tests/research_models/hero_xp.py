"""Research-only event fields and bounded models, never full actor state or native execution."""
import math
import struct

BINARY_SHA256 = 'd6717c157f1608c896255a4bc9290a819d428f1f6d9fb1605c65ebb8e6f620cc'

def level_delta_payload(payload):
    """Read proven first eight bytes, preserve opaque trailer; recorded != applied."""
    if len(payload) not in (8,14):
        raise ValueError('unsupported level payload length')
    actor, requested_delta = struct.unpack_from('>II', payload)
    return {'actor_id': actor, 'requested_level_delta': requested_delta,
            'opaque_trailer_hex': bytes(payload[8:]).hex(), 'applied_delta': None,
            'absolute_level': None, 'recording_build_matched': False}

def ordinary_level_transition(level, requested_delta, xp_progress, xp_required):
    """Only ordinary integral effective level, finite nonnegative XP, no modifiers.

    This is an illustrative branch/arithmetic model, not a native float32/SSE
    emulator. Other stat growth, callbacks and mutation layers are not modeled.
    """
    if isinstance(level,bool) or not isinstance(level,int) or not 0 <= level <= 12:
        raise ValueError('ordinary integral effective level required')
    if isinstance(requested_delta,bool) or not isinstance(requested_delta,int) or not 0 <= requested_delta <= 0xffffffff:
        raise ValueError('unsigned 32-bit delta required')
    if any(not math.isfinite(v) or v<0 for v in (xp_progress,xp_required)):
        raise ValueError('finite nonnegative XP operands required')
    if level>=12:
        return dict(level=level, applied_delta=0, xp_progress=xp_progress, recalculation_path=False)
    delta=min(requested_delta,12-level)
    new_level=level+delta
    # Level1 initialization resets progress. Other recalculation paths subtract
    # ONE old threshold, including zero delta; no invented per-delta loop.
    xp=0.0 if new_level==1 else max(0.0,xp_progress-xp_required)
    return dict(level=new_level,applied_delta=delta,xp_progress=xp,recalculation_path=True)

def xp_target_ratio(progress,required):
    """Raw HUD target only; cached animated display is intentionally not returned."""
    if not math.isfinite(progress) or not math.isfinite(required) or progress<0 or required<=0:
        raise ValueError('finite progress and positive threshold required')
    return min(1.0,max(0.0,progress/required))
