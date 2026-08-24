import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import vendors as R  # noqa: E402

# vendors whose to_config() emits a "vendor" key, and the expected value
EXPECTED_VENDOR = {
    "openai": "openai",
    "azure": "azure",
    "gemini": "gemini",
    "xai": "xai",
    "vertexai": "vertexai",
}


def _dummy_env(name):
    return {var: "dummy" for var in R.required_env(name)}


def test_every_vendor_constructs_and_emits_config():
    for name in R.available():
        vendor = R.build_vendor(name, _dummy_env(name))
        cfg = vendor.to_config()
        assert isinstance(cfg, dict) and cfg, f"{name}: empty config"
        if name in EXPECTED_VENDOR:
            assert cfg.get("vendor") == EXPECTED_VENDOR[name], f"{name}: vendor mismatch"


def test_byo_vendor_missing_creds_raises():
    byo = [n for n in R.available() if R.required_env(n)]
    assert byo, "expected at least one BYO vendor"
    name = byo[0]
    try:
        R.build_vendor(name, {})
    except ValueError as e:
        assert R.required_env(name)[0] in str(e)
    else:
        raise AssertionError(f"{name} should raise when creds are absent")


def test_azure_openai_realtime_uses_the_required_deployment_settings():
    config = R.build_vendor(
        "azure",
        {
            "AZURE_OPENAI_API_KEY": "azure-key",
            "AZURE_OPENAI_REALTIME_URL": "wss://example.openai.azure.com/openai/realtime",
            "AZURE_OPENAI_REALTIME_MODEL": "gpt-realtime-2",
        },
    ).to_config()
    assert config["vendor"] == "azure"
    assert config["url"] == "wss://example.openai.azure.com/openai/realtime"
    assert config["params"] == {
        "model": "gpt-realtime-2",
        "voice": "alloy",
        "instructions": "You are a Conversational AI Agent, developed by Agora.",
    }
    assert config["output_modalities"] == ["audio"]
    assert config["max_history"] == 20
