from typing import List
from pydantic import BaseModel

class ErrorModel(BaseModel):
    """
    A model representing an error with a message and an optional code.

    Attributes:
        message (str): The error message.
        code (int, optional): An optional error code.
        output_buffer (str, optional): An optional buffer containing the terminal output.
    """
    message: str
    code: int | None = None
    output_buffer: str | None = None