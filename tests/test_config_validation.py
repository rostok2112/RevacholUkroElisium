from pathlib import Path
import tempfile
import textwrap
import unittest

from scripts.validate_config import validate_config_file


ROOT = Path(__file__).resolve().parents[1]


class ConfigValidationTests(unittest.TestCase):
    def test_example_config_validates_in_example_mode(self) -> None:
        errors = validate_config_file(ROOT / "config/revachol.example.toml", example=True)
        self.assertEqual([], errors)

    def test_game_install_inside_repo_is_rejected(self) -> None:
        config = """
        [paths]
        game_install_path = "data/local/fake-game"
        local_workspace_path = "workspace"

        [translation]
        quality_mode = "maximum_quality"

        [overlay]
        default_mode = "minimal_hint"

        [llm]
        paid_runtime_allowed = true

        [network_enrichment]
        enabled = false
        lawful_opt_in_required = true
        cache_path = "workspace/network-cache"
        """
        errors = _validate_temp_config(config)
        self.assertTrue(any("game_install_path" in error for error in errors))

    def test_public_repo_cache_path_is_rejected(self) -> None:
        config = """
        [paths]
        game_install_path = ""
        local_workspace_path = "docs/public-cache"

        [translation]
        quality_mode = "maximum_quality"

        [overlay]
        default_mode = "minimal_hint"

        [llm]
        paid_runtime_allowed = true

        [network_enrichment]
        enabled = false
        lawful_opt_in_required = true
        cache_path = "workspace/network-cache"
        """
        errors = _validate_temp_config(config, example=True)
        self.assertTrue(any("approved ignored private root" in error for error in errors))

    def test_inline_secret_is_rejected(self) -> None:
        config = """
        [paths]
        game_install_path = ""
        local_workspace_path = "workspace"

        [translation]
        quality_mode = "maximum_quality"

        [overlay]
        default_mode = "minimal_hint"

        [llm]
        api_key = "sk-test-secret"

        [network_enrichment]
        enabled = false
        lawful_opt_in_required = true
        cache_path = "workspace/network-cache"
        """
        errors = _validate_temp_config(config, example=True)
        self.assertTrue(any("secret" in error for error in errors))


def _validate_temp_config(content: str, *, example: bool = False) -> list[str]:
    with tempfile.TemporaryDirectory() as temp_dir:
        path = Path(temp_dir) / "revachol.toml"
        path.write_text(textwrap.dedent(content), encoding="utf-8")
        return validate_config_file(path, example=example)


if __name__ == "__main__":
    unittest.main()
