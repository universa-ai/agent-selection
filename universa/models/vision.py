import json
import base64
from io import BytesIO

from PIL import Image

from .openai import OpenAI

from .schemas.openai import OpenAIOutput
from .schemas.vision import OpenAIVisionMessage, OpenAIVisionInput
from ..schema import Schema

from ..utils._types import *


class OpenAIVision(OpenAI):
    """
    Basic class for OpenAI vision model.
    """
    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
        input_schema: Optional[Type[Schema]] = None,
        output_schema: Optional[Type[Schema]] = None,
        message_schema: Optional[Type[Schema]] = None,
        **model_kwargs: Any
    ) -> None:
        """
        Initialize the API instance with the given base URL. If no API key is provided,
        it will be looked for in the environment variables.

        Args:
            base_url (str): Base URL for the API.
            api_key (str): API key for the given OpenAI protocol supporting API.
            model_name (Optional[str]): Model name for the API.
            input_schema (Optional[OpenAIVisionInput]): Input schema for the API.
            output_schema (Optional[OpenAIOutput]): Output schema for the API.
            message_schema (Optional[OpenAIVisionMessage]): Message schema for the API.
            model_kwargs (Any): Additional keyword arguments.
                To see a complete list of model arguments, see schemas.openai.OpenAIConstructor.
        """
        # Retrieve API & base URL
        self.api_key = api_key or self.retrieve_env_key(
            env_name=["OPENROUTER_API_KEY"]
        )
        # Retrieve API & base URL
        self.base_url = base_url or self.retrieve_env_key(
            env_name=["OPENROUTER_BASE_URL"]
        )

        super().__init__(
            base_url=self.base_url,
            api_key=self.api_key,
            model_name=model_name or "openai/gpt-4o",
            input_schema=input_schema or OpenAIVisionInput,
            output_schema=output_schema or OpenAIOutput,
            message_schema=message_schema or OpenAIVisionMessage,
            **model_kwargs 
        )

    def create_message(
            self, 
            role: str, 
            content: Union[str, Schema, Dict[str, str]]
    ) -> Optional[Union["Schema", Dict[str, Any]]]:
        """
        Create a message for the OpenAI Vision API.

        Args:
            role (str): Role of the message.
            content (str): Content of the message.

        Returns:
            OpenAIResponse: Message dictionary with role and content.
        """
        if isinstance(content, str):
            return self.message_schema.validate(
                dict(role=role, content=content),
                to_dict=False
            )
        elif isinstance(content, Schema):
            content = json.dumps(content.dict())
            return self.message_schema.validate(
                dict(role=role, content=content),
                to_dict=False
            )
        elif isinstance(content, list):
            return self.message_schema.validate(
                dict(role=role, content=content),
                to_dict=False
            )
        
        return None
        
    def _validate_quality(self, quality: str) -> str:
        """
        Validate the quality of the image.

        Args:
            quality (str): Quality of the image.

        Returns:
            str: Quality of the image if fits one of the categories, raises error otherwise.
        """
        if quality not in ["auto", "low", "high"]:
            raise ValueError(" ".join([
                "The quality of the image can be either 'auto', 'low', 'high'."
            ]))

        return quality
    
    def encode_image(self, image: Image.Image, image_type: Literal['jpeg', 'png']) -> str:
        """
        Encode the image to base64.

        Args:
            image (Image.Image): Image to be encoded.
            image_type (str): Type of the image.

        Returns:
            str: Base64 encoded image.
        """
        with BytesIO() as buffered:
            image.save(buffered, format="PNG" if image_type == "png" else "JPEG")
            image = base64.b64encode(buffered.getvalue())
            image = str(image.decode("utf-8"))

        return f"data:image/{image_type};base64,{image}"
        
    def create_query(
            self,
            inquiry: str,
            images: Optional[Union[List[str], List[Image.Image]]] = None,
            image_qualities: Union[str, List[str]] = "auto"
    ) -> Union[List[Dict[str, Any]], str]:
        """
        Create a message query containing image.

        Args:
            inquiry (str): Inquiry for the image.
            images (List[str] or List[Image.Image]): List of image URLs or base64 encoded strings.
            image_qualities (Union[str, List[str]]): Quality of the images.

        Returns:
            List[Dict[str, Any]]: Query for the image to text model.
        """
        if images is None:
            return inquiry
        
        if isinstance(image_qualities, list) and len(image_qualities) != len(images):
            raise ValueError(" ".join([
                "The number of qualities must match the number of images.",
                "The quality can be either 'auto', 'low', 'high'."
            ]))

        image_queries = []

        # For each images validate the quality and create the query
        for i, image_url in enumerate(images):
            if isinstance(image_qualities, str):
                image_quality = self._validate_quality(image_qualities)
            elif isinstance(image_qualities, list):
                image_quality = self._validate_quality(image_qualities[i])

            image_queries.append({
                "type": "image_url",
                "image_url": {
                    "url": image_url if isinstance(image_url, str) else self.encode_image(image_url, "png"),
                    "detail": image_quality
                }
            })

        return [
            {
                "type": "text",
                "text": inquiry
            },
            *image_queries
        ]
    