from pydantic import BaseModel


class AIAdviceOut(BaseModel):
    status: str  # Np. "CRITICAL", "WARNING", "STABLE"
    summary: str  # Krótkie podsumowanie kondycji firmy jednym zdaniem
    analysis: str  # Głęboka analiza finansowa w formacie Markdown