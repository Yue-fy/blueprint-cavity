"""Reproducible controls for Harbor 0.26; never read private verifier files."""
import json
import shlex
from harbor.agents.nop import NopAgent

SCIENCE_REFERENCE = '''import json,sys
from fractions import Fraction
from pathlib import Path
p=json.loads(Path(sys.argv[1]).read_text())
g,c,A=(Fraction(p[k]) for k in ('g','c','A'))
d=1-abs(g)*(abs(c)+2*abs(A))
if not (d>0 and d*d>32*g*g):
    raise ValueError('Outside the reviewed Case A parameter regime')
v=g*g/(2*(1-g*(c+2*A))**2)
Path(sys.argv[2]).write_text(json.dumps({'value':float(v),'confidence':1,
 'rationale':'Case A singular coefficient: g^2 / (2 (1-g(c+2A))^2); exact rational input. See science_demo/proof.md for the reviewed regime.'}))
'''


class CaseAReferenceAgent(NopAgent):
    """Task-family analytic policy using only the supplied neutral input.json."""
    @staticmethod
    def name(): return 'case-a-analytic-reference'

    async def run(self, instruction, environment, context):
        result = await environment.exec(
            'python3 -c ' + shlex.quote(SCIENCE_REFERENCE) +
            ' /workspace/input.json /workspace/answer.json', timeout_sec=20)
        if result.return_code != 0:
            raise RuntimeError('Case A reference command failed')


class StopEarlyAgent(NopAgent):
    """Read-only first observation, then explicit zero-confidence abstention.

    This policy is distinct from no-op and from interrupting a model at a time
    budget: it exercises the published abstention contract without solving.
    """
    @staticmethod
    def name(): return 'observe-then-abstain'

    async def run(self, instruction, environment, context):
        observation = await environment.exec('ls -1 /workspace', timeout_sec=20)
        if observation.return_code != 0:
            raise RuntimeError('Stop-early observation failed')
        if 'rationale' in instruction and 'Diagonal coefficient limit' in instruction:
            answer = {'value':None, 'confidence':0, 'rationale':'Stopped after the first observation.'}
        else:
            answer = {'value':None, 'unit':'m2', 'confidence':0, 'evidence':[],
                      'assumptions':['Stopped after the first observation.']}
        code = 'from pathlib import Path; Path("/workspace/answer.json").write_text(' + repr(json.dumps(answer)) + ')'
        result = await environment.exec('python3 -c ' + shlex.quote(code), timeout_sec=20)
        if result.return_code != 0:
            raise RuntimeError('Stop-early submission failed')
