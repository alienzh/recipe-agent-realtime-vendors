import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import agent as a  # noqa: E402


def test_agent_constructs():
    os.environ.setdefault("AGORA_APP_ID", "x")
    os.environ.setdefault("AGORA_APP_CERTIFICATE", "y")
    inst = a.Agent()
    # default realtime vendor; no creds validated in __init__ (BYO-only recipe)
    assert inst.vendor == "openai"
