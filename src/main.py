"""
This script will take a reddit URL and use OpenAI's GPT-3 model to generate
a summary of the reddit thread.
"""
# Import necessary modules
import os
import re
from typing import Tuple, List, Union
import openai
from dotenv import load_dotenv
from src.utils import get_token_length, request_json_from_url, save_output


load_dotenv()

# number of tokens to summarize to
MAX_CHUNK_SIZE = 2500
MAX_NUMBER_OF_SUMMARIES = 1

# OpenAI Constants
MAX_TOKENS = 4000
GPT_MODEL = "text-davinci-003"

# reddit URL/ IMPORTANT to add .json to the end of the URL
REDDIT_URL = (
    "https://www.reddit.com/r/"
    "politics/comments/102a8k0/discussion_thread_2023_speaker_of_the_united.json"
)

INSTRUCTION_TEXT = "Edit the article to include relevant information from \
the comments, revise and enhance the content, and make it engaging and easy \
to understand. Avoid including code or commands, and present facts objectively \
and clearly."

openai.organization = os.environ.get("OPENAI_ORG_ID")
openai.api_key = os.environ.get("OPENAI_API_KEY")


def get_metadata_from_reddit_json(data: dict) -> Tuple[str, str]:
    """
    Get the title and selftext from the reddit json data.
    """
    child_data = data[0]["data"]["children"][0]["data"]
    if "title" not in child_data:
        raise ValueError("Title not found in child data")
    if "selftext" not in child_data:
        raise ValueError("Selftext not found in child data")
    return child_data["title"], child_data["selftext"]


def get_body_contents(
    data: Union[List[Union[dict, str]], dict], path: List[str]
) -> List[Tuple[str, str]]:
    """
    Generator function that yields tuples of the form (path, body_content) for
    all dictionaries in the input data with a key of 'body'.
    NOTE: path is potentially useful here for indenting the output
    """
    # If data is a dictionary, check if it has a 'body' key
    if isinstance(data, dict):
        if "body" in data:
            # If the dictionary has a 'body' key, yield the path and value of the 'body' key
            path_str = "/".join([str(x) for x in path])
            yield path_str, data["body"]
        # Iterate through the dictionary's key-value pairs
        for key, value in data.items():
            # Recursively call the function with the value and updated path
            yield from get_body_contents(value, path + [key])
    # If data is a list, iterate through the elements
    elif isinstance(data, list):
        for index, item in enumerate(data):
            # Recursively call the function with the element and updated path
            yield from get_body_contents(item, path + [str(index)])


def concatenate_bodies(contents: List[Tuple[str, str]]) -> List[str]:
    """
    Concatenate the bodies into an array of newline delimited strings that are
    <MAX_CHUNK_SIZE tokens long
    """
    results = []
    result = ""
    for body_tuple in contents:
        if body_tuple[1]:
            # replace one or more consecutive newline characters
            body_tuple = (body_tuple[0], re.sub(r"\n+", "\n", body_tuple[1]))
            result += body_tuple[1] + "\n"
            if get_token_length(result) > MAX_CHUNK_SIZE:
                results.append(result)
                result = ""
    if result:
        results.append(result)
    return results


def complete_chunk(prompt: str) -> str:
    """
    Use OpenAI's GPT-3 model to complete a chunk of text based on the given prompt.

    Args:
        prompt (str): The prompt to use as the starting point for text completion.

    Returns:
        str: The completed chunk of text.
    """
    print("prompt=" + prompt)
    print("token length: " + str(get_token_length(prompt)))
    response = openai.Completion.create(
        model=GPT_MODEL,
        prompt=prompt,
        temperature=0.9,
        max_tokens=MAX_TOKENS - get_token_length(prompt),
    )
    return response.choices[0].text


def generate_summary(title: str, selftext: str, groups: List[str]) -> str:
    """
    Generate a summary of the reddit thread using OpenAI's GPT-3 model.
    """

    # initialize the prefix with the title and selftext of the reddit thread JSON
    prefix = f"Title: {title}\n{selftext}"

    # Use f-strings for string formatting
    output = f"START\n\n{INSTRUCTION_TEXT}\n\n"

    # use the first group twice because of top comments
    groups.insert(0, groups[0])

    # Use enumerate to get the index and the group in each iteration
    for i, group in enumerate(groups[:MAX_NUMBER_OF_SUMMARIES]):
        # Use triple quotes to create a multi-line string
        prompt = f"""{prefix}

{INSTRUCTION_TEXT}

COMMENTS BEGIN
{group}
COMMENTS END

Title:"""
        summary = complete_chunk(prompt)
        # insert the summary into the prefix
        prefix = f"{title}\n\n{summary}\nEND"
        # Use format method to insert values into a string
        output += f"\n\n============\nSUMMARY COUNT: {i}\n============\n"
        output += f"PROMPT: {prompt}\n\n{summary}\n======================================\n\n"

    return output


def main():
    """
    Main function.
    """
    reddit_json = request_json_from_url(REDDIT_URL)

    # write raw json output to file for debugging
    with open("output.json", "w", encoding="utf-8") as raw_json_file:
        raw_json_file.write(str(reddit_json))

    # Get the title and selftext from the reddit thread JSON
    title, selftext = get_metadata_from_reddit_json(reddit_json)

    # get an array of body contents
    contents = get_body_contents(reddit_json, [])

    # concatenate the bodies into an array of newline delimited strings
    groups = concatenate_bodies(contents)

    # Generate the summary
    output = generate_summary(title, selftext, groups)

    print(output)

    save_output(title, output)


if __name__ == "__main__":
    main()
