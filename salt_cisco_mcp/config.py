import os
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field
from pydantic_settings import BaseSettings, PydanticBaseSettingsSource, SettingsConfigDict

_DEFAULT_YAML_PATH = "/etc/salt/mcp/config.yaml"
_DEFAULT_REDACT_KEYS = [
    "password",
    "passwd",
    "pass",
    "secret",
    "enable_password",
    "enable_secret",
    "api_key",
    "api-key",
    "token",
    "auth_token",
    "bearer",
    "bearer_token",
    "community",
    "snmp_community",
    "tacacs_key",
    "radius_key",
    "shared_secret",
    "pre_shared_key",
    "psk",
    "passphrase",
    "private_key",
    "credential",
    "credentials",
]


class ServerConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    transport: Literal["stdio", "http"] = "stdio"
    http_host: str = "127.0.0.1"
    http_port: int = 7842
    allow_write: bool = False
    confirm_token: str = ""


class PathsConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    doc_db: str = "/var/lib/salt-mcp/docs.db"
    recipes: str = "/usr/share/salt-mcp/recipes"
    log_file: str = "/var/log/salt-mcp/server.log"
    audit_log: str = "~/.salt-mcp/audit.jsonl"
    live_cache: str = "/var/lib/salt-mcp/live-cache"


class SaltMasterConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    master_config: str = "/etc/salt/master"
    proxy_dir: str = "/etc/salt/proxy.d"
    pillar_roots: list[str] = Field(default_factory=lambda: ["/etc/salt/pillar"])
    file_roots: list[str] = Field(default_factory=lambda: ["/srv/salt"])
    salt_call_path: str = "salt-call"
    salt_key_path: str = "salt-key"
    command_timeout_s: int = 30


class EmbeddingsConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    enabled: bool = True
    model: str = "BAAI/bge-small-en-v1.5"
    device: str = "cpu"


class RerankerConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    enabled: bool = False
    model: str = "BAAI/bge-reranker-base"


class RetrievalConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    default_tier: str = "focused"
    default_max_tokens: int = 1500
    default_response_tokens: int = 2000
    hard_cap_tokens: int = 8000
    embeddings: EmbeddingsConfig = Field(default_factory=EmbeddingsConfig)
    reranker: RerankerConfig = Field(default_factory=RerankerConfig)
    rrf_k: int = 60
    low_confidence_bm25: float = 1.0
    low_confidence_cosine: float = 0.55


class NetworkConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    enabled: bool = True
    live_fallback: bool = True
    upstream_base: str = "https://docs.saltproject.io/en/3007"
    rate_limit_per_min: int = 60
    user_agent: str = "salt-cisco-mcp/1.0"
    request_timeout_s: int = 15
    live_cache_ttl_s: int = 3600


class ScrapeConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rps: int = 2
    max_pages: int = 5000
    follow_redirects: bool = True
    schedule: str = "weekly"


class HttpAuthConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    mode: str = "none"
    bearer_token_file: str = "/etc/salt/mcp/bearer.token"


class SecurityConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    redact_keys: list[str] = Field(default_factory=lambda: list(_DEFAULT_REDACT_KEYS))
    http_auth: HttpAuthConfig = Field(default_factory=HttpAuthConfig)
    bind_local_only: bool = True
    max_input_bytes: int = 262144


class LoggingConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    format: Literal["json", "console"] = "json"


class TelemetryConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    enabled: bool = True
    metrics_dir: str = "/var/lib/salt-mcp"


class _YamlConfigSource(PydanticBaseSettingsSource):
    def __init__(self, settings_cls: type[BaseSettings], yaml_path: str) -> None:
        super().__init__(settings_cls)
        self._yaml_path = yaml_path

    def get_field_value(self, field: Any, field_name: str) -> tuple[Any, str, bool]:  # noqa: ANN401
        return None, field_name, False

    def __call__(self) -> dict[str, Any]:
        p = Path(self._yaml_path)
        if not p.exists():
            return {}
        with p.open(encoding="utf-8") as fh:
            data = yaml.safe_load(fh)
        return data if isinstance(data, dict) else {}


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="SALT_MCP_",
        env_nested_delimiter="__",
        extra="forbid",
    )

    server: ServerConfig = Field(default_factory=ServerConfig)
    paths: PathsConfig = Field(default_factory=PathsConfig)
    salt_master: SaltMasterConfig = Field(default_factory=SaltMasterConfig)
    retrieval: RetrievalConfig = Field(default_factory=RetrievalConfig)
    network: NetworkConfig = Field(default_factory=NetworkConfig)
    scrape: ScrapeConfig = Field(default_factory=ScrapeConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    telemetry: TelemetryConfig = Field(default_factory=TelemetryConfig)

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        yaml_path = os.environ.get("SALT_MCP_CONFIG_FILE", _DEFAULT_YAML_PATH)
        yaml_src = _YamlConfigSource(settings_cls, yaml_path)
        # dotenv_settings and file_secret_settings intentionally omitted:
        # this server is configured via YAML file + env vars only.
        return init_settings, env_settings, yaml_src
