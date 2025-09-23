

import os
import tempfile
import pytest
from pydantic import ValidationError

from bookverse_core.config import BaseConfig, ConfigLoader
from bookverse_core.config.validation import (
    validate_environment,
    validate_log_level,
    sanitize_config_for_logging
)


class DemoDemoTestConfig(BaseConfig):
    test_string: str = "default_value"
    test_int: int = 42
    test_bool: bool = True
    test_list: list = ["default"]


class TestBaseConfig:

    def test_base_config_defaults(self):
        config = BaseConfig()

        assert config.service_name == "BookVerse Service"
        assert config.service_version == "1.0.0"
        assert config.environment == "development"
        assert config.debug is False
        assert config.log_level == "INFO"
        assert config.auth_enabled is True

    def test_base_config_custom_values(self):
        config = BaseConfig(
            service_name="Custom Service",
            service_version="2.0.0",
            environment="production",
            debug=True,
            log_level="DEBUG"
        )

        assert config.service_name == "Custom Service"
        assert config.service_version == "2.0.0"
        assert config.environment == "production"
        assert config.debug is True
        assert config.log_level == "DEBUG"

    def test_base_config_validation(self):
        config = BaseConfig(log_level="WARNING")
        assert config.log_level == "WARNING"

        config = BaseConfig(log_level="INVALID")
        assert config.log_level == "INVALID"

    def test_config_to_dict(self):
        config = BaseConfig(service_name="Test Service")
        config_dict = config.to_dict()

        assert isinstance(config_dict, dict)
        assert config_dict["service_name"] == "Test Service"
        assert "service_version" in config_dict
        assert "environment" in config_dict


class DemoTestConfigLoader:

    def test_config_loader_defaults_only(self):
        loader = ConfigLoader(DemoDemoTestConfig)
        config = loader.load_from()

        assert config.test_string == "default_value"
        assert config.test_int == 42
        assert config.test_bool is True
        assert config.test_list == ["default"]

    def test_config_loader_with_overrides(self):
        loader = ConfigLoader(DemoTestConfig)
        config = loader.load_from(
            defaults={
                "test_string": "override_value",
                "test_int": 100,
                "test_bool": False
            }
        )

        assert config.test_string == "override_value"
        assert config.test_int == 100
        assert config.test_bool is False

    def test_config_loader_with_yaml_file(self, temp_config_file):
        loader = ConfigLoader(BaseConfig)
        config = loader.load_from(yaml_file=temp_config_file)

        assert config.service_name == "Test Service from YAML"
        assert config.debug is False
        assert config.log_level == "INFO"

    def test_config_loader_with_env_vars(self):
        test_env = {
            "TEST_TEST_STRING": "env_value",
            "TEST_TEST_INT": "200",
            "TEST_TEST_BOOL": "false"
        }

        original_env = {}
        for key, value in test_env.items():
            original_env[key] = os.environ.get(key)
            os.environ[key] = value

        try:
            loader = ConfigLoader(DemoTestConfig)
            config = loader.load_from(env_prefix="TEST_")

            assert config.test_string == "env_value"
            assert config.test_int == 200
            assert config.test_bool is False
        finally:
            for key, original_value in original_env.items():
                if original_value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = original_value

    def test_config_loader_precedence(self, temp_config_file):
        os.environ["TEST_SERVICE_NAME"] = "From Environment"

        try:
            loader = ConfigLoader(BaseConfig)
            config = loader.load_from(
                yaml_file=temp_config_file,
                env_prefix="TEST_",
                defaults={"service_name": "From Defaults"},
                overrides={"service_name": "From Overrides"}
            )

            assert config.service_name == "From Overrides"
        finally:
            os.environ.pop("TEST_SERVICE_NAME", None)

    def test_config_loader_missing_yaml_file(self):
        loader = ConfigLoader(DemoTestConfig)
        config = loader.load_from(yaml_file="nonexistent.yaml")

        assert config.test_string == "default_value"

    def test_config_loader_invalid_yaml_file(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("invalid: yaml: content: [")
            temp_path = f.name

        try:
            loader = ConfigLoader(DemoTestConfig)
            config = loader.load_from(yaml_file=temp_path)
            assert config.test_string == "default_value"
        finally:
            os.unlink(temp_path)

    def test_config_loader_caching(self):
        loader = ConfigLoader(DemoTestConfig)

        config1 = loader.load_from(defaults={"test_string": "cached_value"})

        config2 = loader.load_from(defaults={"test_string": "cached_value"})

        assert config1 is config2
        assert config1.test_string == "cached_value"

    def test_config_loader_cache_invalidation(self):
        loader = ConfigLoader(DemoTestConfig)

        config1 = loader.load_from(defaults={"test_string": "value1"})

        config2 = loader.load_from(defaults={"test_string": "value2"})

        assert config1 is not config2
        assert config1.test_string == "value1"
        assert config2.test_string == "value2"


class DemoTestConfigValidation:

    def test_validate_environment_valid(self):
        assert validate_environment("development") is True
        assert validate_environment("staging") is True
        assert validate_environment("production") is True

    def test_validate_environment_invalid(self):
        assert validate_environment("invalid") is False
        assert validate_environment("") is False
        assert validate_environment(None) is False

    def test_validate_log_level_valid(self):
        assert validate_log_level("DEBUG") is True
        assert validate_log_level("INFO") is True
        assert validate_log_level("WARNING") is True
        assert validate_log_level("ERROR") is True
        assert validate_log_level("CRITICAL") is True

    def test_validate_log_level_invalid(self):
        assert validate_log_level("INVALID") is False
        assert validate_log_level("debug") is False
        assert validate_log_level("") is False
        assert validate_log_level(None) is False

    def test_sanitize_config_for_logging(self):
        config_dict = {
            "service_name": "Test Service",
            "database_url": "postgresql://user:password@host:5432/db",
            "api_key": "secret-api-key",
            "auth_secret": "super-secret",
            "debug": True,
            "log_level": "INFO"
        }

        sanitized = sanitize_config_for_logging(config_dict)

        assert sanitized["service_name"] == "Test Service"
        assert sanitized["debug"] is True
        assert sanitized["log_level"] == "INFO"

        assert sanitized["database_url"] == "***"
        assert sanitized["api_key"] == "***"
        assert sanitized["auth_secret"] == "***"

    def test_sanitize_config_nested_dict(self):
        config_dict = {
            "service": {
                "name": "Test Service",
                "secret_key": "secret-value"
            },
            "database": {
                "host": "localhost",
                "password": "secret-password"
            }
        }

        sanitized = sanitize_config_for_logging(config_dict)

        assert sanitized["service"]["name"] == "Test Service"
        assert sanitized["database"]["host"] == "localhost"

        assert sanitized["service"]["secret_key"] == "***"
        assert sanitized["database"]["password"] == "***"


class DemoTestConfigIntegration:

    def test_full_config_loading_workflow(self, temp_config_file):
        os.environ["DEMO_DEBUG"] = "true"
        os.environ["DEMO_LOG_LEVEL"] = "DEBUG"

        try:
            loader = ConfigLoader(BaseConfig)
            config = loader.load_from(
                yaml_file=temp_config_file,
                env_prefix="DEMO_",
                defaults={"service_description": "Default description"},
                overrides={"environment": "test"}
            )

            assert config.service_name == "Test Service from YAML"
            assert config.debug is True
            assert config.log_level == "DEBUG"
            assert config.service_description == "Default description"
            assert config.environment == "test"

        finally:
            os.environ.pop("DEMO_DEBUG", None)
            os.environ.pop("DEMO_LOG_LEVEL", None)
