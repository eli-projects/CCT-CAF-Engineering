"""Run the retained skill's construction regressions in the reference suite."""
import importlib.util
from pathlib import Path
path=Path(__file__).resolve().parents[2]/"skills/create-cct-caf/tests/test_retained_workflow.py"
spec=importlib.util.spec_from_file_location("retained_workflow_tests",path)
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
RetainedWorkflowTests=module.RetainedWorkflowTests
