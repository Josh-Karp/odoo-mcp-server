from src.mcp_server import ALLOWED_MODELS, _validate_domain, _validate_model


class TestValidateModel:
    def test_valid_model(self):
        result = _validate_model(ALLOWED_MODELS[0])
        assert result is None

    def test_model_not_in_allowlist(self):
        result = _validate_model("invalid.model")
        assert result is not None
        assert isinstance(result, str)

    def test_empty_string(self):
        result = _validate_model("")
        assert result is not None

    def test_none_value(self):
        result = _validate_model(None)
        assert result is not None

    def test_integer_value(self):
        result = _validate_model(123)
        assert result is not None


class TestValidateDomain:
    def test_empty_domain(self):
        result = _validate_domain([])
        assert result is None

    def test_valid_non_or_domain(self):
        result = _validate_domain([("name", "=", "test")])
        assert result is None

    def test_valid_or_with_few_conditions(self):
        domain = ["|", ("name", "=", "a"), ("name", "=", "b")]
        result = _validate_domain(domain)
        assert result is None

    def test_valid_or_with_five_conditions(self):
        domain = [
            "|",
            ("f", "=", 1),
            ("f", "=", 2),
            ("f", "=", 3),
            ("f", "=", 4),
            ("f", "=", 5),
        ]
        result = _validate_domain(domain)
        assert result is None

    def test_invalid_or_with_too_many_conditions(self):
        domain = [
            "|",
            ("f", "=", 1),
            ("f", "=", 2),
            ("f", "=", 3),
            ("f", "=", 4),
            ("f", "=", 5),
            ("f", "=", 6),
        ]
        result = _validate_domain(domain)
        assert result is not None
        assert isinstance(result, str)

    def test_non_list_domain(self):
        result = _validate_domain("not a list")
        assert result is not None
        assert isinstance(result, str)
