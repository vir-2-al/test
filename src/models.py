from pydantic import BaseModel, Field, ConfigDict

class UserLoginScheme(BaseModel):
    username: str = Field(
        min_length=5,
        max_length=20,
        description='User login')
    password: str = Field(
        min_length=8,
        max_length=20,
        description='User password')
    model_config = ConfigDict(extra='forbid')

class UserInfoScheme(UserLoginScheme):
    id: int = Field(
        ge=0
    )
    first_name: str | None = Field(
        max_length=50,
        description='First name')
    middle_name: str | None = Field(
        max_length=50,
        description='Middle name')
    last_name: str | None = Field(
        max_length=50,
        description='Last name')
    company: str | None = Field(
        max_length=50,
        description='Company name')
    job_title: str | None = Field(
        max_length=50,
        description='Job title')
    model_config = ConfigDict(extra='forbid')