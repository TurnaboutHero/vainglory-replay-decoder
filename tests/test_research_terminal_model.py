"""Synthetic native-control-flow model; not a replay/player emulator."""
import json
import unittest

PRIMARY_EDGES={(0,1),(0,2),(1,0),(1,2),(1,3),(2,3)}
SECONDARY_EDGES={(0,1),(1,2),(1,0),(2,0),(2,3)}
class TerminalModel:
    def __init__(self, primary=1, secondary=2, selected_team=1, alternative=False):
        self.primary,self.secondary=primary,secondary
        self.selected_team,self.alternative=selected_team,alternative
        self.raw_team=self.raw_reason=None
        self.result_callbacks=[]
        self.trace=[]
    def end(self, team, reason):
        self.raw_team,self.raw_reason=team&255,reason
        self.trace.append('overwrite_fields')
        if self.primary is None or (self.primary,2) in PRIMARY_EDGES:
            self.trace.append(f'exit_primary_{self.primary}')
            self.primary=2
            self.trace.append('commit_primary_2')
            self.result_callbacks.append({'relative_win':self.raw_team==(1 if self.alternative else self.selected_team),'reason':reason})
            self.trace.append('enter_primary_2_result_callback')
        else:
            self.trace.append('primary_transition_rejected')
        if self.secondary is None or (self.secondary,3) in SECONDARY_EDGES:
            self.secondary=3
            self.trace.append('commit_secondary_3')
        else:
            self.trace.append('secondary_transition_rejected')
    def snapshot(self):
        return vars(self)
class Tests(unittest.TestCase):
    def test_first_then_conflicting_repeat(self):
        m=TerminalModel();m.end(1,0);m.end(2,2)
        self.assertEqual((m.raw_team,m.raw_reason),(2,2))
        self.assertEqual(m.result_callbacks,[{'relative_win':True,'reason':0}])
    def test_callback_before_secondary(self):
        m=TerminalModel();m.end(2,0)
        self.assertLess(m.trace.index('enter_primary_2_result_callback'),m.trace.index('commit_secondary_3'))
    def test_primary_rejection_does_not_stop_secondary(self):
        m=TerminalModel(primary=3);m.end(2,0)
        self.assertEqual(m.result_callbacks,[]);self.assertEqual(m.secondary,3)
    def test_first_request_not_guaranteed_accepted(self):
        m=TerminalModel(primary=2);m.end(1,0)
        self.assertEqual(m.result_callbacks,[])
    def test_mode_changes_relative_result(self):
        a=TerminalModel(selected_team=2);b=TerminalModel(selected_team=2,alternative=True)
        a.end(2,0);b.end(2,0)
        self.assertTrue(a.result_callbacks[0]['relative_win']);self.assertFalse(b.result_callbacks[0]['relative_win'])
    def test_state_zero_can_enter_terminal(self):
        m=TerminalModel(primary=0,secondary=0);m.end(1,0)
        self.assertEqual(len(m.result_callbacks),1);self.assertEqual(m.secondary,0)
    def test_ui_banner_reason_domain(self):
        def key(win,reason):
            return ('VICTORY' if win else 'DEFEAT') if reason==0 else 'SURRENDER' if reason==2 else None
        self.assertEqual(key(True,2),'SURRENDER');self.assertIsNone(key(True,1))
if __name__ == '__main__':
    unittest.main()
