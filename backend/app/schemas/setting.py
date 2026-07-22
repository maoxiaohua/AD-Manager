from pydantic import BaseModel
from typing import Optional


class SettingResponse(BaseModel):
    key: str
    value: str

    model_config = {"from_attributes": True}


class SettingsUpdateRequest(BaseModel):
    """Bulk update for settings. Each key-value pair corresponds to a Setting row."""
    settings: dict[str, str]


class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str
