"""
Base models and utilities for MongoDB integration.

Provides PyObjectId type for proper ObjectId serialization with Pydantic.
"""

from pydantic import BaseModel, Field, ConfigDict
from bson import ObjectId
from typing import Any, Optional
from datetime import datetime


class PyObjectId(ObjectId):
    """
    Custom ObjectId type for Pydantic.

    Allows Pydantic to properly serialize/deserialize MongoDB ObjectIds.
    """

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v, _info=None):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

    @classmethod
    def __get_pydantic_core_schema__(cls, _source_type: Any, _handler):
        from pydantic_core import core_schema

        return core_schema.json_or_python_schema(
            json_schema=core_schema.str_schema(),
            python_schema=core_schema.union_schema(
                [
                    core_schema.is_instance_schema(ObjectId),
                    core_schema.chain_schema(
                        [
                            core_schema.str_schema(),
                            core_schema.no_info_plain_validator_function(cls.validate),
                        ]
                    ),
                ]
            ),
            serialization=core_schema.plain_serializer_function_ser_schema(
                lambda x: str(x)
            ),
        )


class BaseDBModel(BaseModel):
    """
    Base model for all database documents.

    Provides common fields that all documents should have:
    - _id: MongoDB ObjectId
    - created_at: Creation timestamp
    - updated_at: Last update timestamp
    """

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str},
    )

    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    def model_dump(self, **kwargs) -> dict:
        """
        Override model_dump to handle ObjectId serialization.
        """
        data = super().model_dump(**kwargs)
        if self.id is not None:
            data["_id"] = str(self.id)
        return data
