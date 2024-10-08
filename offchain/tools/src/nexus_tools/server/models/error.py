# coding: utf-8

from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, Field


class Error(BaseModel):
    """NOTE: This class is auto generated by OpenAPI Generator (https://openapi-generator.tech).

    Do not edit the class manually.

    Error - a model defined in OpenAPI

        message: The message of this Error [Optional].
        code: The code of this Error [Optional].
    """

    message: Optional[str] = Field(alias="message", default=None)
    code: Optional[int] = Field(alias="code", default=None)


Error.update_forward_refs()
