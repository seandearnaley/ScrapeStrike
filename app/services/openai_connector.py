"""OpenAI Connector."""
import os
import openai
from config import ConfigVars
from data_types.summary import GenerateSettings
from env import EnvVarsLoader
from log_tools import Logger
from openai import OpenAI

client = OpenAI()
config = ConfigVars()
app_logger = Logger.get_app_logger()
env_vars = EnvVarsLoader.load_env()

openai.organization = env_vars["OPENAI_ORG_ID"]
openai.api_key = env_vars["OPENAI_API_KEY"]


@Logger.log
def complete_openai_text(
    prompt: str,
    max_tokens: int,
    settings: GenerateSettings,
) -> str:
    """
    Use OpenAI's GPT model to complete text based on the given prompt.

    Args:
        prompt (str): The prompt to use as the starting point for text completion. # noqa: E501
        max_tokens (int, optional): The maximum number of tokens to generate in the
        response.
        settings (GenerateSettings): The settings to use for generating the text.

    Returns:
        str: The completed text.
    """

    try:
        common_args = {
            "model": settings["selected_model"],
            "max_tokens": max_tokens,
        }

        response = openai.chat.completions.create(
            **common_args,
            messages=[
                {"role": "system", "content": settings["system_role"]},
                {"role": "user", "content": prompt},
            ],
        )

        # if not isinstance(response, OpenAIObject):
        #     raise ValueError("Invalid Response")

        if response.choices:
            content = response.choices[0].message.content
            return content.strip()

        return "Response doesn't have choices or choices have no text."

    except openai.OpenAIError as err:
        return f"OpenAI Error: {err}"









    except ValueError as err:
        return f"Value error: {err}"
