from pydantic import BaseModel, Field

from app.schemas.organization import OrganizationCreate
from app.schemas.user import RegisterUserCreate, UserOut


class TokenOut(BaseModel):
    access_token: str = Field(..., description="Token JWT do autoryzacji w Swaggerze (przycisk Authorize)")
    token_type: str = Field(default="bearer", examples=["bearer"])


class RegisterCompanyRequest(BaseModel):
    company_data: OrganizationCreate
    user_data: RegisterUserCreate

    model_config = {
        "json_schema_extra": {
            "example": {
                "company_data": {"name": "Serwis Rowerowy Sp. z o.o."},
                "user_data": {
                    "email": "admin@firma.pl",
                    "password": "SuperTajneHaslo123!",
                },
            }
        }
    }
