from copy import deepcopy
from pathlib import Path
import json
import os
import tempfile
import unittest
from unittest.mock import patch
from scripts import railway_owner_study_cutover_once as m


def receipt():
    return {'operation_id':m.SOURCE_OP,'status':'completed','cutoff_utc':m.CUT_TEXT,
            'files':[{'name':name,'after_bytes':0} for name in
                     ('engine_events.jsonl','error_events.jsonl','fsm_events.jsonl')]}


def row(when, **kw):
    return {'created_ts':when,'state':'FINAL','observation':{'outcome':'WIN','observed_ts':when+0.1}, **kw}


def state(records=None):
    return {'protocol':m.PROTOCOL,'records':records if records is not None else {
        'old':row(float(m.CUT)-20), 'new':row(float(m.CUT)+20)},
        'started_ts':float(m.CUT)-100,'capacity_rejections':0,'scope':{'unchanged':True}}


def fixture_validator(value):
    # Deliberately synthetic; the real validator is required by production main.
    if value.get('protocol') != m.PROTOCOL or not isinstance(value.get('records'),dict):
        raise ValueError('synthetic_schema')
    if any(r.get('state') not in {'FINAL','OBSERVING'} for r in value['records'].values()):
        raise ValueError('synthetic_schema')


class PlanTests(unittest.TestCase):
    def test_removes_only_old(self):
        report,crossed,bound=m.plan(state(),receipt(),fixture_validator)
        self.assertEqual(set(crossed['records']),{'new'})
        self.assertEqual(report['old_records_removed'],1)
        self.assertFalse(bound['records'])
    def test_source_unchanged(self):
        before=state(); original=deepcopy(before)
        m.plan(before,receipt(),fixture_validator)
        self.assertEqual(before,original)
    def test_boundary_evidence_separated_without_mutation(self):
        s=state(); s['records']['old']['receipt']={'api_accepted_ts':float(m.CUT)+1}
        report,candidate,bound=m.plan(s,receipt(),fixture_validator)
        self.assertEqual(bound['records']['old'],s['records']['old'])
        self.assertNotIn('old',candidate['records'])
        self.assertEqual(report['old_records_removed'],0)
        self.assertEqual(report['boundary_records_preserved_separately'],1)
    def test_pending_old_blocks(self):
        s=state();s['records']['old']['observation']['outcome']='PENDING'
        with self.assertRaisesRegex(ValueError,'IN_FLIGHT'):m.plan(s,receipt(),fixture_validator)
    def test_old_observing_blocks(self):
        s=state();s['records']['old']['state']='OBSERVING'
        with self.assertRaisesRegex(ValueError,'IN_FLIGHT'):m.plan(s,receipt(),fixture_validator)
    def test_new_pending_preserved(self):
        s=state();s['records']['new']['state']='OBSERVING';s['records']['new']['observation']['outcome']='PENDING'
        _,c,_=m.plan(s,receipt(),fixture_validator)
        self.assertEqual(c['records']['new'],s['records']['new'])
    def test_equality_preserved(self):
        s=state({'equal':row(float(m.CUT))})
        self.assertIn('equal',m.plan(s,receipt(),fixture_validator)[1]['records'])
    def test_wrong_receipt_blocks(self):
        r=receipt();r['cutoff_utc']='2026-11-10T15:00:00+00:00'
        with self.assertRaises(ValueError):m.plan(state(),r,fixture_validator)
    def test_nonzero_old_log_receipt_blocks(self):
        r=receipt();r['files'][0]['after_bytes']=1
        with self.assertRaises(ValueError):m.plan(state(),r,fixture_validator)
    def test_boolean_clock_blocks(self):
        s=state();s['records']['old']['received_ts']=True
        with self.assertRaises(ValueError):m.plan(s,receipt(),fixture_validator)
    def test_naive_clock_blocks(self):
        with self.assertRaises(ValueError):m.stamp('2026-11-10T13:00:00')
    def test_invalid_clock_even_after_late_clock_blocks(self):
        s=state();s['records']['old'].update(received_ts=float(m.CUT)+1,late_ts='invalid')
        with self.assertRaises(ValueError):m.plan(s,receipt(),fixture_validator)
    def test_validator_rejection_blocks(self):
        def no(_):raise ValueError('canonical_rejected')
        with self.assertRaisesRegex(ValueError,'canonical_rejected'):m.plan(state(),receipt(),no)
    def test_changed_candidate_rejected(self):
        def no(v):
            if m.MARKER in v: raise ValueError('changed')
        with self.assertRaisesRegex(ValueError,'changed'):m.plan(state(),receipt(),no)
    def test_scope_and_outcomes_unchanged(self):
        s=state();_,c,_=m.plan(s,receipt(),fixture_validator)
        self.assertEqual(c['scope'],s['scope']);self.assertEqual(c['records']['new'],s['records']['new'])
    def test_duplicate_keys_block(self):
        with self.assertRaisesRegex(ValueError,'DUPLICATE'):m.strict(b'{"a":1,"a":2}')
    def test_nonfinite_block(self):
        with self.assertRaises(ValueError):m.strict(b'{"a":NaN}')
    def test_overflow_block(self):
        with self.assertRaises(ValueError):m.strict(b'{"a":1e999}')
    def test_reserved_receipt_blocks(self):
        s=state();s['records']['old']['study_delivery']={'entry':{'status':'RESERVED'}}
        with self.assertRaises(ValueError):m.plan(s,receipt(),fixture_validator)
    def test_unresolved_delivery_blocks(self):
        s=state();s['records']['old']['study_delivery']={'entry':{'status':'API_ACCEPTED'}}
        with self.assertRaises(ValueError):m.plan(s,receipt(),fixture_validator)

class FilesystemTests(unittest.TestCase):
    def setUp(self):
        self.t=tempfile.TemporaryDirectory();self.root=Path(self.t.name)
        self.source=self.root/m.REL;self.source.parent.mkdir(parents=True)
        (self.root/'state').mkdir()
        self.source.write_bytes(m.encode(state()))
        (self.root/'state'/(m.SOURCE_OP+'.json')).write_bytes(m.encode(receipt()))
    def tearDown(self):self.t.cleanup()
    def test_dry_run_no_writes(self):
        before={p: p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        self.assertEqual(m.run(self.root,fixture_validator)['status'],'dry_run_validated')
        after={p: p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        self.assertEqual(before,after)
    def test_apply_and_replay_preserves_new_growth(self):
        r=m.run(self.root,fixture_validator,apply=True)
        self.assertEqual(r['status'],'completed')
        now=m.read_regular(self.source);now['records']['later']=row(float(m.CUT)+500)
        self.source.write_bytes(m.encode(now));before=self.source.read_bytes()
        r=m.run(self.root,fixture_validator,apply=True)
        self.assertFalse(r['repeated_deletion']);self.assertEqual(before,self.source.read_bytes())
    def test_boundary_persisted_before_source(self):
        s=state();s['records']['old']['late_ts']=float(m.CUT)+1
        self.source.write_bytes(m.encode(s));m.run(self.root,fixture_validator,apply=True)
        boundary=m.read_regular(self.root/'state'/(m.OP+'-boundary-evidence.json'))
        self.assertEqual(boundary['records']['old'],s['records']['old'])
    def test_claimed_receipt_never_replays(self):
        p=self.root/'state'/(m.OP+'.json');p.write_bytes(m.encode({'operation_id':m.OP,'status':'claimed'}))
        before=self.source.read_bytes()
        with self.assertRaises(ValueError):m.run(self.root,fixture_validator,apply=True)
        self.assertEqual(before,self.source.read_bytes())
    def test_symlink_source_refused(self):
        other=self.source.with_name('other.json');self.source.rename(other);self.source.symlink_to(other)
        with self.assertRaises(ValueError):m.run(self.root,fixture_validator,apply=True)
    def test_hardlink_source_refused(self):
        os.link(self.source,self.source.with_name('linked.json'))
        with self.assertRaises(ValueError):m.run(self.root,fixture_validator,apply=True)
    def test_source_change_before_commit_refused(self):
        original=m.create_durable
        def changed(path,value):
            original(path,value)
            if str(path).endswith('.tmp'):
                s=state();s['records']['later']=row(float(m.CUT)+800)
                self.source.write_bytes(m.encode(s))
        with patch.object(m,'create_durable',side_effect=changed):
            with self.assertRaisesRegex(ValueError,'SOURCE_CHANGED'):m.run(self.root,fixture_validator,apply=True)
        self.assertIn('later',m.read_regular(self.source)['records'])
    def test_commit_failure_does_not_redelete(self):
        original=os.replace
        def fail_complete(a,b):
            if str(a).endswith('.completed.tmp'):raise OSError('simulated')
            return original(a,b)
        with patch.object(m.os,'replace',side_effect=fail_complete):
            with self.assertRaises(OSError):m.run(self.root,fixture_validator,apply=True)
        before=self.source.read_bytes()
        with self.assertRaises(ValueError):m.run(self.root,fixture_validator,apply=True)
        self.assertEqual(before,self.source.read_bytes())

if __name__=='__main__':unittest.main()
