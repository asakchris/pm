from typing import Annotated, Literal

from pydantic import BaseModel, Field, field_validator


class ColumnCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    position: int | None = None


class ColumnUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    position: int | None = None


class CardCreate(BaseModel):
    column_id: int
    title: str = Field(..., min_length=1, max_length=500)
    details: str = Field(default="", max_length=5000)
    position: int | None = None


class CardUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=500)
    details: str | None = Field(default=None, max_length=5000)
    column_id: int | None = None
    position: int | None = None


class ChatHistoryItem(BaseModel):
    role: Literal["user", "assistant"]
    content: str


def _validate_numeric_id(value: str, field_name: str) -> str:
    if not value.isdigit():
        raise ValueError(f"{field_name} must be a numeric string, got {value!r}")
    return value


class CreateCardAction(BaseModel):
    type: Literal["create_card"]
    columnId: str
    title: str = Field(..., min_length=1, max_length=500)
    details: str = Field(default="", max_length=5000)
    position: int | None = None

    @field_validator("columnId")
    @classmethod
    def column_id_must_be_numeric(cls, v: str) -> str:
        return _validate_numeric_id(v, "columnId")


class UpdateCardAction(BaseModel):
    type: Literal["update_card"]
    cardId: str
    title: str | None = Field(default=None, min_length=1, max_length=500)
    details: str | None = Field(default=None, max_length=5000)

    @field_validator("cardId")
    @classmethod
    def card_id_must_be_numeric(cls, v: str) -> str:
        return _validate_numeric_id(v, "cardId")


class MoveCardAction(BaseModel):
    type: Literal["move_card"]
    cardId: str
    columnId: str
    position: int | None = None

    @field_validator("cardId", "columnId")
    @classmethod
    def ids_must_be_numeric(cls, v: str) -> str:
        return _validate_numeric_id(v, "id")


class DeleteCardAction(BaseModel):
    type: Literal["delete_card"]
    cardId: str

    @field_validator("cardId")
    @classmethod
    def card_id_must_be_numeric(cls, v: str) -> str:
        return _validate_numeric_id(v, "cardId")


ChatAction = Annotated[
    CreateCardAction | UpdateCardAction | MoveCardAction | DeleteCardAction,
    Field(discriminator="type"),
]


class StructuredChatOutput(BaseModel):
    reply: str
    actions: list[ChatAction] = Field(default_factory=list)


class ChatRequest(BaseModel):
    message: str
    history: list[ChatHistoryItem] = Field(default_factory=list)
    apply_updates: bool = True


class ChatResponse(BaseModel):
    response: str
    actions: list[ChatAction] = Field(default_factory=list)
    board: dict | None = None
    model: str | None = None
