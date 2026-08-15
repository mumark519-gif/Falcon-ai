from pydantic import BaseModel,Field
class AgentRequest(BaseModel):
    goal:str=Field(min_length=1)
    context:dict|None=None
    provider:str|None=None
    autonomous:bool=False
