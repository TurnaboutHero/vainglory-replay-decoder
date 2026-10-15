import hashlib,json,subprocess,sys,time
from pathlib import Path
from vg.decoder_v2.player_state import decode_player_state
src=Path(sys.argv[1]); out=Path(sys.argv[2]); out.mkdir(parents=True,exist_ok=True)
files=sorted(src.glob('*.vgr'),key=lambda p:int(p.name.split('.')[-2])); replay=files[0]
def hashes(): return {p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
before=hashes(); combined=hashlib.sha256(b''.join(p.read_bytes() for p in files)).hexdigest()
results={}
for label,ids in [('all',None),('selected',[1500,1501])]:
 cmd=[sys.executable,'-B','-m','vg.decoder_v2.decode_match',str(replay),'--at-game-time','600','-o',str(out/f'{label}-cli.json')]
 for actor in ids or []: cmd+=['--player-id',str(actor)]
 run=subprocess.run(cmd,capture_output=True,text=True); (out/f'{label}-cli.log').write_text(run.stdout+run.stderr)
 assert run.returncode==0,(run.returncode,run.stderr)
 api=decode_player_state(replay,at_game_time=600,player_ids=ids).to_dict(); (out/f'{label}-api.json').write_text(json.dumps(api,ensure_ascii=False,indent=2)+'\n')
 cli=json.loads((out/f'{label}-cli.json').read_text()); api=json.loads(json.dumps(api))
 results[label]={'exit_code':run.returncode,'cli_api_equal':cli==api,'player_count':len(api['players']),'support_status':api['support_status'],'record_boundary':api['record_boundary'],'query_timing':api['query_timing'],'definitive_analysis':api['definitive_analysis']}
 print(label,results[label],flush=True)
a=json.loads((out/'all-api.json').read_text()); s=json.loads((out/'selected-api.json').read_text()); subset=[p for p in a['players'] if p['native_actor_id'] in (1500,1501)]
summary={'commit':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),'source_sections':len(files),'source_bytes':sum(p.stat().st_size for p in files),'concatenated_sha256':combined,'source_hashes_unchanged':hashes()==before,'queries':results,'selected_rows_equal_all_subset':s['players']==subset,'visible_inventory_entries':sum(len(p['items']) for p in a['players']),'actor1507':next(p for p in a['players'] if p['native_actor_id']==1507),'limitations':['Offline CLI/API consistency only; no new client execution, native capture, rendered-screen or final-result validation','Historical comparison used dbb5718; this run uses main without its additive actor/skin split']}
(out/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n'); (out/'source-hashes.json').write_text(json.dumps(before,indent=2)+'\n'); print('DONE',flush=True)
