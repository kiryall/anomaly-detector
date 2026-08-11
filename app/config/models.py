from pydantic import BaseModel, ConfigDict, Field

SUPPURTED_EXTENSIONS = {".pt", ".pth", ".onnx"}

class UserSettings(BaseModel):
    """Настройки пользователя."""

    model_config = ConfigDict(validate_assignment=True)

    model: str = ""

    confidence: float = Field(default=0.40, ge=0.0, le=1.0)

    iou: float = Field(default=0.50, ge=0.0, le=1.0)

    copy_images: bool = True

    save_database: bool = True

    last_folder: str = ""

    theme: str = "dark"