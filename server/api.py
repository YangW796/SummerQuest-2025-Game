from pydantic import BaseModel

class StartGameRequest(BaseModel):
    key: str

class PlayCardRequest(BaseModel):
    key: str
    card_id: int