# Extended time, scheduler and ultimate follow-up

Base326582d; selected LAA SHA256d6717c157f1608c896255a4bc9290a819d428f1f6d9fb1605c65ebb8e6f620cc.
Addresses are preferred-image VAs; +offsets are hexadecimal. Fresh acquisition
numbers below refer to EXTENDED_REA_RECEIPT.json, not function discovery counts.

## Start and next checks

01_COOLDOWN and earlier CLOCK-HUD establish QPC raw delta capped at2 before scale,
float32 publication020ec6d0, per-timer+28 pause, stage4 timer callback and unknown
historical replay time partition. Next checks were global writers, registry owner,
pre/post-stage maintenance, and concrete hero selectors rather than another timer dump.

## Actual publication writer and network control

Fresh004 xrefs finds getter0112a7a0 and writer0112ba0c inside0112b9e0.007 xrefs
bounds publication guard020ec6dc to getter0112aa70,setter0112ab90,initialization
0112b794 and update0112b9f0.016/017 show setter and three direct calling procedures:
004bf650 clears it;004c0380 clears it during selected cleanup;004bfdc0 accepts input.
032/033/034 identify conditional veto: if a game session exists,00938fb0 returns
0209e208 and00936100 reads its definition byte+27. Nonzero+27 returns before
publication guard assignment.00936170 reads a different byte+21, controlling a
secondary004dade0 call. Neither flag is named a universal pause permission here.
074 assembly confirms the early return and setter call004bfde4.

The two004bfdc0 callsites resolve to004cfec0 receive cases0470 and047c (059,
064/065). Each copies ONE payload byte,normalizes nonzero to1,then passes it
through004bfdc0 to0112ab90.004c0de0 is a singleton getter (092),not another
state setter despite misleading unused decompiler arguments; raw callsites
preserve the argument across that getter and place its result in ECX.
0470 additionally invokes00548bf0;047c does not.093 shows00548bf0 can request
primary state1 from state0 and sets session+19d bit2 (mask4). It does not set
that byte's clock-gate bit0. Thus the two inputs must not be collapsed into a
single certified UI pause event. No replay framing length, historical build
identity,UI pause-button origin or actual native execution was established.

013 xrefs01a761b0 finds only already known getter/three setter paths in the
analysed reference inventory. No new simulation-scale writer is claimed.

## Registry, dispatch and delayed retirement

008 registry xrefs led to046 (interior0112b780 resolves0112b410) and1020112ade0.
Initialization allocates020ec828 as a pointer/count pair.0112ade0 builds zeroed
0x17c-stride descriptors,invokes a supplied registration callback,copies registered
descriptors to allocated storage,initializes their pools and publishes pointer/count.
This connects type registration to the actual scheduler registry. It is not a new
wall-clock frequency. Context/arena registry020ec81c is separate from020ec828.

009 and0900112a3c0 connect prior mark-only0112a080 to later cleanup: inspect marked
bitmap+178,optionally call descriptor+4,dispatch attached object listeners+8,invoke
descriptor+60,clear object generation+4,clear bitmap and update active-index pool
bookkeeping. Removal is deferred until this maintenance pass; the mark function
alone did not prove immediate destruction. Existing0112b850 calls maintenance
around per-type stage dispatch.01000943900 is merely ECX+4!=0,used for different
queue objects; naming that getter a global pause check would be unsupported.

Fresh091 assembly corroborates stage2 before the020ec6dc test. If guard is zero,
new scaled/raw deltas are published,then stages3/4/5 and associated drains run.
If guard is nonzero,stage2 still ran and published delta remains unchanged while
those later stages are skipped. This refutes whole-loop-stop semantics. The
previous-versus-new published delta distinction remains a phase issue,not a
universal transform from replay record timestamps. Per-timer pause,scale0,
publication guard and session clock gate are four distinct controls.

## Ultimate resource graph and fallback boundary

EXTENDED_HERO_GRAPH.json contains fresh hashed local CFF checks: inline actor+4c,
component+18 relocated ordered list,selectors+24/+28/+2c,and third selected
ability +0/+10 localization keys. Catherine1/2/3 selects C atINST+e2c;
Ozo0/3/8 selects C+1740;Varya0/4/8 selects C+16e0;Ringo0/1/2 selects C+a5c.
The selector values corroborate the prior catalog; fresh evidence is the concrete
resource identity,embedded location and key relocation. The scan decoded only
four selected actor resources. Actual translated text and a generic ultimate
flag were not established. Actor-wide learnUltimate audio and C suffix are not
sufficient. Runtime ability overrides remain separate from initial UI selection.

011 ability-descriptor references contain prior allocation/registration sites;
no new ultimate-specific meaning follows from that type ID.012 fallback020ea218
references and038/049 show it is used when runtime ability/state is absent and
also outside ability UI (ping/taunt key fallback). Its complete initialization
was not recovered. It is not evidence that missing ability,state key,empty-name
hash or ultimate identities are interchangeable.

## Closure and falsification

Closed: selected network operand-to-publication-control bridge and veto,registry
publication,marked-object retirement,per-stage ordering,and four selected-resource
identity checks. Unclosed: historical replay clock partition,actual pause UI,
hero-specific successful ultimate activation and runtime override identity.
No decoder/time reducer change is justified from these alone.

Falsify with a matched-build trace of0470/047c raw bytes,definition+27,guard before/
after,stage2 and3/4/5 calls,new/old published delta,session+19d and timer+28. Compare
0470's state1 request separately. For ultimate bind actor generation,loaded resource,
dynamic display list,selected key,rank,complete reason mask,request and received apply.
Changing descriptor stride/callbacks or resource relocation reopens the static bridge.
