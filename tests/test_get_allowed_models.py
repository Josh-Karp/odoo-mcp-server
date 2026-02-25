from src.mcp_server import get_allowed_models, ALLOWED_MODELS


class TestGetAllowedModels:
    def test_returns_dict(self):
        result = get_allowed_models()
        assert isinstance(result, dict)

    def test_has_models_key(self):
        result = get_allowed_models()
        assert "models" in result

    def test_models_is_list(self):
        result = get_allowed_models()
        assert isinstance(result["models"], list)

    def test_models_is_non_empty(self):
        result = get_allowed_models()
        assert len(result["models"]) > 0

    def test_count_equals_len_models(self):
        result = get_allowed_models()
        assert result["count"] == len(result["models"])

    def test_models_matches_allowed_models(self):
        result = get_allowed_models()
        assert result["models"] == ALLOWED_MODELS

    def test_expected_models_present(self):
        result = get_allowed_models()
        assert "res.partner" in result["models"]
        assert "sale.order" in result["models"]
        assert "crm.lead" in result["models"]

    def test_no_error_key(self):
        result = get_allowed_models()
        assert "error" not in result
