"""Utility functions for the Reddit Scraper project."""
import json
import os
import re
import sys
from datetime import datetime
from typing import Any, Dict

import requests
import tiktoken

HEADERS = {"User-Agent": "Mozilla/5.0"}


def num_tokens_from_string(string: str, encoding_name: str = "gpt2") -> int:
    """
    Returns the number of tokens in a text string.
    https://help.openai.com/en/articles/4936856-what-are-tokens-and-how-to-count-them
    """
    encoding = tiktoken.get_encoding(encoding_name)
    num_tokens = len(encoding.encode(string))
    return num_tokens


def generate_filename(title) -> str:
    """Generate a filename from the given title."""
    # Remove all special characters and spaces from the title
    filename = re.sub(r"[^\w\s]", "", title)
    # Replace all remaining spaces with underscores
    filename = filename.replace(" ", "_")
    # Shorten the filename if it is too long
    if len(filename) > 100:
        filename = filename[:100]
    return filename


def request_json_from_url(url: str) -> Dict[str, Any]:
    """
    Make a request to the given URL and return the JSON response.
    """
    json_data = {}
    try:
        with requests.get(url, headers=HEADERS, timeout=10) as response:
            response.raise_for_status()
            try:
                json_data = response.json()
            except json.decoder.JSONDecodeError as err:
                print(f"There was an error decoding the JSON response: {err}")

                sys.exit(1)
    except requests.exceptions.RequestException as err:
        print(f"There was an error making the request: {err}")
        sys.exit(1)

    return json_data


def get_timestamp() -> str:
    """Get a timestamp in the format YYYYMMDDHHMMSS."""
    return datetime.now().strftime("%Y%m%d%H%M%S")


def save_output(title: str, output: str) -> str:
    """
    Save the output to a file in current working dir. The filename will
    be the generated from the title, santized with a timestamp appended to it.
    """
    # Get the current working directory
    cwd = os.getcwd()

    # Define the relative path to the output folder
    output_folder = "outputs"

    # Construct the full path to the output folder
    output_path = os.path.join(cwd, output_folder)

    # Create the output folder if it does not exist
    os.makedirs(output_path, exist_ok=True)

    # Create the output filename with a timestamp
    output_filename = f"{generate_filename(title)}_{get_timestamp()}.txt"

    # Construct the full path to the output file
    output_file_path = os.path.join(output_path, output_filename)

    with open(output_file_path, "w", encoding="utf-8") as output_file:
        output_file.write(output)

    return output_file_path


def estimate_word_count(num_tokens):
    """
    Given the number of GPT-2 tokens, estimates the real word count.
    """
    # The average number of real words per token for GPT-2 is 0.56, according to OpenAI.
    # Multiply the number of tokens by this average to estimate the total number of real
    # words.
    estimated_word_count = round(num_tokens * 0.56)

    return estimated_word_count
