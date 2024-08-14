from ...schema import Schema
from .openai import (
    OpenAIToolCallMessage,
    OpenAIOutputMessage, 
    OpenAIToolChoice
)

from ..message import BaseMessage
from ...utils._types import *


class VisionImageUrl(Schema):
    url: str = Field(description="The URL of the image.")
    detail: Literal["auto", "low", "high"] = Field(
        description="The detail of the image.", 
        default="auto"
    )

class VisionImageContent(Schema):
    """
    Vision content schema. They contain all the configs that OpenAI vision completion accepts.
    """
    type: str = Field(
        description="The type of the content.",
        default="image_url"
    )
    image_url: VisionImageUrl = Field(description="The image URL of the content.")

class VisionTextContent(Schema):
    """
    Vision content schema. They contain all the configs that OpenAI vision completion accepts.
    """
    type: str = Field(
        description="The type of the content.", 
        default="text"
    )
    text: str = Field(description="The text data of the content.")

class OpenAIVisionMessage(BaseMessage):
    """
    Vision message schema. They contain all the configs that OpenAI vision completion accepts.
    Note that the content field validation is ignored for less complexity.

    Learn more about ignoring validation from here: 
    https://docs.pydantic.dev/2.0/api/functional_validators/#pydantic.functional_validators.SkipValidation 
    """
    role: Literal["user", "assistant", "system"] = Field(
        description="The role of the author of this message."
    )

    # NOTE: SerializeAsAny is necessary here to avoid the warning caused by the model_dump() method.
    # Pydantic considers it as a bug in their own code. 
    content: SerializeAsAny[Annotated[
        Union[str, List[Union[VisionTextContent, VisionImageContent]]], 
        SkipValidation
    ]] = Field(
        description="The contents of the message.",
    )

    @field_validator("content")
    @classmethod
    def validate_content(cls, value: List[Dict[str, Any]]):
        """
        Validate the content field. 
        This is necessary because we are skipping validation at the beginning.
        """

        if isinstance(value, list):
            new_content = []
            for item in value:
                if item["type"] == "text":
                    new_content.append(VisionTextContent(**item))
                elif item["type"] == "image_url":
                    new_content.append(VisionImageContent(**item))
                else:
                    raise ValueError("Invalid content type. Content must be a str, VisionTextContent or VisionImageContent.")
            return new_content
        elif isinstance(value, str):
            return value
        else:
            raise ValueError("Invalid content type. Content must be a str, VisionTextContent or VisionImageContent.")

class OpenAIVisionInput(Schema):
    """
    OpenAI API input schema. They contain all the configs that OpenAI chat completion accepts.
    """
    messages: List[Union[
        OpenAIVisionMessage,
        OpenAIOutputMessage,
        OpenAIToolCallMessage
    ]] = Field(description="A list of messages comprising the conversation so far.")
    model: str = Field(description="The model to use.")
    tools: Optional[List[JsonSchemaValue]] = Field(
        description="A list of tools the model may call. Currently, only functions are supported as a tool. Use this to provide a list of functions the model may generate JSON inputs for.", 
        default=None
    )
    tool_choice: Optional[Union[Literal["none", "auto"], OpenAIToolChoice]] = Field(
        description="Controls which (if any) function is called by the model. If not provided, the model will choose a function to call.", 
        default=None
    )
    max_tokens: Optional[int] = Field(
        description="The maximum number of [tokens](/tokenizer) that can be generated in the chat completion.", 
        default=None
    )
    temperature: Optional[float] = Field(
        description="What sampling temperature to use, between 0 and 2. Higher values like 0.8 will make the output more random, while lower values like 0.2 will make it more focused and deterministic.",
        default=None
    )
    top_p: Optional[float] = Field(
        description="An alternative to sampling with temperature, called nucleus sampling, where the model considers the results of the tokens with top_p probability mass. So 0.1 means only the tokens comprising the top 10% probability mass are considered.",
        default=1.0
    )
    frequency_penalty: Optional[float] = Field(
        description="Number between -2.0 and 2.0. Positive values penalize new tokens based on their existing frequency in the text so far, decreasing the model's likelihood to repeat the same line verbatim.",
        default=0.0
    )
    presence_penalty: Optional[float] = Field(
        description="Number between -2.0 and 2.0. Positive values penalize new tokens based on whether they appear in the text so far, increasing the model's likelihood to talk about new topics.",
        default=0.0
    )
    stop: Union[str, List[str]] = Field(
        description="Up to 4 sequences where the API will stop generating further tokens.", 
        default=None
    )
    response_format: Optional[JsonSchemaValue] = Field(
        description="An object specifying the format that the model must output. Compatible with GPT-4 Turbo and gpt-3.5-turbo-1106.",
        default=None
    )
    model_config = ConfigDict(
        protected_namespace=()
    )
