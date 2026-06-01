import os
from unittest.mock import patch

def test_openrouter_free_models_augmentation():
    # Ensure OPENROUTER_API_KEY is set to bypass interactive prompt
    os.environ["OPENROUTER_API_KEY"] = "dummy"

    from hermes_cli.main import _model_flow_openrouter

    base_models = ["anthropic/claude-opus-4.7"]
    pricing_data = {
        "tencent/hy3-preview:free": {"input": 0, "output": 0},
        "openrouter/owl-alpha": {"input": 0, "output": 0},
        "nvidia/nemotron-3-nano-30b-a3b:free": {"input": 0, "output": 0},
        "openai/gpt-4": {"input": 0.03, "output": 0.06},
    }

    with patch("hermes_cli.models.model_ids", return_value=base_models), \
         patch("hermes_cli.models.get_pricing_for_provider", return_value=pricing_data), \
         patch("hermes_cli.auth._prompt_model_selection", return_value=None) as mock_prompt, \
         patch("hermes_cli.auth._save_model_choice"), \
         patch("hermes_cli.auth.deactivate_provider"), \
         patch("hermes_cli.config.load_config", return_value={}), \
         patch("hermes_cli.config.save_config"):
        _model_flow_openrouter({}, current_model="")

    # Extract the models list passed to _prompt_model_selection
    models_passed = mock_prompt.call_args[0][0]
    assert "anthropic/claude-opus-4.7" in models_passed
    assert "tencent/hy3-preview:free" in models_passed
    assert "openrouter/owl-alpha" in models_passed
    assert "nvidia/nemotron-3-nano-30b-a3b:free" in models_passed
    # Non-free model should not be added (even if present in pricing it would not be included)
    assert "openai/gpt-4" not in models_passed
