"""Conditional configuration arithmetic, never an HP damage/stack simulator.

Only selected four-array getter and named-prefix declaration arithmetic are
represented. Activation, native stub execution, caps and server mitigation
are deliberately outside this model.
"""
import math
import struct


def f32(value):
    value=float(value)
    if not math.isfinite(value):
        raise ValueError("Finite witness inputs required")
    return struct.unpack("<f",struct.pack("<f",value))[0]


def effective_layer_value(base, additive, total_percent, additive_percent):
    """Algebraic 00937480 witness, not instruction-rounding equivalence."""
    b,a,t,m=map(f32,(base,additive,total_percent,additive_percent))
    return f32((b+(1+m)*a)*(1+t))


def named_prefix_witness(bonesaw=0,tension_bow=0,broken_myth=0):
    """One active cap-one marker per declared name, if lifetime effects apply.

    This assumed state is conditional: queued grant order and actual selected
    behavior dispatch are not simulated. Different item copies keep ordinary
    strength declarations but reuse the assumed active marker set.
    """
    counts=(bonesaw,tension_bow,broken_myth)
    if any(type(n) is not int or n<0 for n in counts) or sum(counts)>6:
        raise ValueError("At most six nonnegative integral item counts")
    spear,bone,tension,shard,myth=map(f32,(.1,.2,.3,.1,.45))
    armor=0.0
    if bonesaw or tension_bow:
        armor=f32(spear+f32(bone-spear))
    if tension_bow:
        armor=f32(armor+f32(tension-bone))
    shield=f32(shard+f32(myth-shard)) if broken_myth else 0.0
    return {"armor_prefix_coefficient":armor,"shield_prefix_coefficient":shield,
            "ordinary_weapon_strength_declared":30*bonesaw+40*tension_bow,
            "ordinary_crystal_strength_declared":50*broken_myth,
            "slots":sum(counts)}
