import argparse
import copy
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
from audit import audit


def selected(data, tag, hook):
    return next(row for row in data['synthetic_controls'][0]['events'] if row['event']['tag'] == tag and row['event'].get('hook') == hook)


def test(folder, workspace=None):
    data = json.loads((folder / 'controls.json').read_text())
    positive = audit(data, folder, workspace)
    cases = [
        ('constructor_operand', lambda bad: selected(bad, 'opcode_hook_before', 'resource_ctor')['event']['arg_bits'].__setitem__(2, 0)),
        ('after_float_bits', lambda bad: selected(bad, 'opcode_hook_after', 'resource_apply')['sample']['player']['gold_balance'].__setitem__('bits', 0)),
        ('apply_dispatch_identity', lambda bad: selected(bad, 'opcode_hook_after', 'resource_apply')['event'].__setitem__('dispatch_id', 999999)),
        ('queue_heap_identity', lambda bad: next(row for row in bad['synthetic_controls'][0]['events'] if row['event']['tag'] == 'opcode_queue_copy')['event'].__setitem__('heap_action', '0x1')),
        ('missing_case', lambda bad: bad['synthetic_controls'].pop()),
        ('natural_source_time', lambda bad: bad['natural_controls'][0]['transitions'][0]['source'].__setitem__('time_bits', 0)),
        ('natural_delta', lambda bad: bad['natural_controls'][0]['transitions'][0]['after']['player']['resource14'].update(value=2, bits=1073741824)),
        ('swapped_visual_image', lambda bad: bad['natural_controls'][0]['visual']['before'].__setitem__('image', 'lane-after.png')),
        ('primary_image_hash', lambda bad: bad['images'][0].__setitem__('sha256', '0' * 64)),
        ('wrong_raw_buffer', lambda bad: bad['raw_receiver_buffer_controls'][0]['events'][1]['event'].__setitem__('buffer_hex', '00' * 12)),
        ('wrong_raw_destination', lambda bad: bad['raw_receiver_buffer_controls'][0]['events'][1]['event'].__setitem__('destination', '0x1')),
        ('false_unique_offset', lambda bad: bad['raw_receiver_buffer_controls'][0].__setitem__('source_offset_unique', True)),
        ('raw_constructor_reader', lambda bad: bad['raw_receiver_buffer_controls'][0]['events'][2]['sample']['replay_reader_after'].__setitem__('section', 99)),
        ('borrowed_resolver', lambda bad: [row['event']['active_hook'].__setitem__('object', '0x1') for row in bad['synthetic_controls'][0]['events'] if row['event']['tag'] == 'opcode_actor_resolve']),
        ('narrowed_original_requirement', lambda bad: bad.__setitem__('original_requirement', 'Resource arithmetic only')),
    ]
    if workspace:
        cases += [
            ('raw_buffer_line_reference', lambda bad: bad['raw_receiver_buffer_controls'][0]['events'][1].__setitem__('line', 1)),
            ('missing_offset_candidate', lambda bad: bad['raw_receiver_buffer_controls'][0]['source_candidates'].pop()),
            ('apply_line_reference', lambda bad: selected(bad, 'opcode_hook_after', 'resource_apply').__setitem__('line', 1)),
            ('source_offset_reference', lambda bad: bad['synthetic_controls'][0]['source'].__setitem__('offset', bad['synthetic_controls'][0]['source']['offset'] + 1)),
            ('natural_sample_line_reference', lambda bad: bad['natural_controls'][0]['transitions'][0]['after'].__setitem__('line', 3)),
        ]
    negatives = []
    for name, mutate in cases:
        bad = copy.deepcopy(data)
        mutate(bad)
        try:
            audit(bad, folder, workspace)
        except AssertionError:
            negatives.append({'case': name, 'rejected': True})
        else:
            raise AssertionError('Tampered control accepted: ' + name)
    return {'ok': True, 'positive': positive, 'negative_cases': negatives, 'negative_count': len(negatives)}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--workspace', type=Path)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    result = test(Path(__file__).resolve().parent, args.workspace)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result))
