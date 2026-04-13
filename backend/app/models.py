from typing import Annotated, Literal

from pydantic import BaseModel, Field


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


class CreateCardAction(BaseModel):
    type: Literal["create_card"]
    columnId: str
    title: str
    details: str = ""
    position: int | None = None


class UpdateCardAction(BaseModel):
    type: Literal["update_card"]
    cardId: str
    title: str | None = None
    details: str | None = None


class MoveCardAction(BaseModel):
    type: Literal["move_card"]
    cardId: str
    columnId: str
    position: int | None = None


class DeleteCardAction(BaseModel):
    type: Literal["delete_card"]
    cardId: str


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
