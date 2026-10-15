"""Synthetic boundaries only; no gameplay or replay classifier."""
def kind_flags(kind, exact_name):
    flags=0
    if kind in (2,3): flags|=0x1000
    if kind==2: flags|=0x8000
    if kind==3: flags|=0x4000 if exact_name=='VainNode' else 0x2000
    return flags

def requests_actor_dead(current_state, actor_resolves=True, apply_mode=True):
    # Request is not proof that the state-machine allowed edge commits.
    return actor_resolves and apply_mode and current_state==3

def regeneration_gate(now,last,producer_mode,secondary_gate,health,limit):
    # Finite inputs only; cadence and exact derived limit are deliberately external.
    return producer_mode and not secondary_gate and now-last>5.0 and health<limit

def observations_die(source_raw):
    return {'source_raw':source_raw,'awarded_killer':None,'awarded_team':None,'winner':None,'cleanup_completed':None}
