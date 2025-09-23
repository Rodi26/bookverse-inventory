

import os
from typing import Any, Dict, Optional, Type, TypeVar
from pathlib import Path

from pydantic import BaseModel, Field, ConfigDict

T = TypeVar('T', bound='BaseConfig')


class BaseConfig(BaseModel):
    
    
    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        validate_assignment=True,
        extra="forbid"
    )
    
    service_name: str = Field(
        default="BookVerse Service",
        description="Name of the service"
    )
    
    service_version: str = Field(
        default="1.0.0",
        description="Version of the service"
    )
    
    service_description: str = Field(
        default="A BookVerse microservice",
        description="Description of the service"
    )
    
    api_version: str = Field(
        default="v1",
        description="API version"
    )
    
    api_prefix: str = Field(
        default="/api/v1",
        description="API path prefix"
    )
    
    environment: str = Field(
        default="development",
        description="Environment (development, staging, production)"
    )
    
    log_level: str = Field(
        default="INFO",
        description="Logging level"
    )
    
    debug: bool = Field(
        default=False,
        description="Enable debug mode"
    )
    
    database_url: Optional[str] = Field(
        default=None,
        description="Database connection URL"
    )
    
    auth_enabled: bool = Field(
        default=True,
        description="Enable authentication"
    )
    
    development_mode: bool = Field(
        default=False,
        description="Enable development mode"
    )
    
    oidc_authority: str = Field(
        default="https://dev-auth.bookverse.com",
        description="OIDC authority URL"
    )
    
    oidc_audience: str = Field(
        default="bookverse:api",
        description="OIDC audience"
    )
    
    jwt_algorithm: str = Field(
        default="RS256",
        description="JWT algorithm"
    )
    
    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"
    
    @property
    def is_development(self) -> bool:
        return self.environment.lower() == "development"
    
    @property
    def is_debug_enabled(self) -> bool:
        return self.debug or self.is_development
    
    def get_api_prefix(self) -> str:
        if self.api_prefix.startswith("/"):
            return self.api_prefix
        return f"/api/{self.api_version}"
    
    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()
    
    @classmethod
    def from_dict(cls: Type[T], data: Dict[str, Any]) -> T:
        return cls(**data)
    
    @classmethod
    def from_env(cls: Type[T], prefix: str = "") -> T:
        
            
        env_vars = {}
        
        for key, value in os.environ.items():
            if prefix and key.startswith(prefix):
                config_key = key[len(prefix):].lower()
                env_vars[config_key] = value
            elif not prefix:
                env_vars[key.lower()] = value
        
        return cls(**env_vars)
    
    def __str__(self) -> str:
        return f"{self.__class__.__name__}(service={self.service_name}, version={self.service_version})"
    
    def __repr__(self) -> str:
        return self.__str__()
