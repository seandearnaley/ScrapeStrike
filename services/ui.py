"""
UI functions
"""
# Import necessary modules


from typing import Any, Dict, Optional, Tuple

from config import (
    APP_TITLE,
    DEFAULT_CHUNK_TOKEN_LENGTH,
    DEFAULT_GPT_MODEL,
    DEFAULT_MAX_TOKEN_LENGTH,
    DEFAULT_NUMBER_OF_SUMMARIES,
    DEFAULT_QUERY_TEXT,
    REDDIT_URL,
)
from services.data import generate_summary_data
from streamlit_setup import st
from utils.common import is_valid_reddit_url, replace_last_token_with_json, save_output
from utils.openai import get_models, num_tokens_from_string


def render_input_box() -> Optional[str]:
    """
    Render the input box for the reddit URL and return its value.
    """
    reddit_url = st.text_area("Enter REDDIT URL:", REDDIT_URL)
    if not is_valid_reddit_url(reddit_url):
        st.error("Please enter a valid Reddit URL")
        return None
    return reddit_url


def render_settings(org_id: str, api_key: str) -> Tuple[str, Dict[str, Any]]:
    """
    Render the settings for the app and return the model and settings.
    """
    with st.expander("Edit Settings"):
        query_text: str = st.text_area("Instructions", DEFAULT_QUERY_TEXT, height=250)

        col1, col2 = st.columns(2)
        with col1:
            models = get_models(org_id, api_key)
            model_ids = [model["id"] for model in models]  # type: ignore
            filtered_list = [
                item
                for item in model_ids
                if "text-davinci" in item
                or "text-curie" in item  # todo add more models
            ]
            print("filtered_list", filtered_list)
            model_ids_sorted = sorted(filtered_list)
            default_model_index = model_ids_sorted.index(DEFAULT_GPT_MODEL)
            selected_model = st.radio(
                "Select Model", model_ids_sorted, default_model_index
            )

            if selected_model:
                st.markdown(
                    f"You selected model {selected_model}. Here are the parameters:"
                )
                st.text(models[model_ids.index(selected_model)])  # type: ignore
            else:
                st.text("Select a model")
                st.stop()

            chunk_token_length = st.number_input(
                "Chunk Token Length", value=DEFAULT_CHUNK_TOKEN_LENGTH, step=1
            )

            number_of_summaries = st.number_input(
                "Number of Summaries",
                value=DEFAULT_NUMBER_OF_SUMMARIES,
                min_value=1,
                max_value=10,
                step=1,
            )

            max_token_length = st.number_input(
                "Max Token Length", value=DEFAULT_MAX_TOKEN_LENGTH, step=1
            )
        with col2:
            st.markdown(
                """
                #### Help
                Enter the instructions for the model to follow.
                It will generate a summary of the Reddit thread.
                The trick here is to experiment with token lengths and number
                of summaries. The more summaries you generate, the more likely
                you are to get a good summary.
                The more tokens you use, the more likely you are to get a good summary.
                The more tokens you use, the longer it will take to generate
                the summary. The more summaries you generate, the more it will cost you.
                """
            )

    return selected_model, {
        "query_text": query_text,
        "chunk_token_length": chunk_token_length,
        "number_of_summaries": number_of_summaries,
        "max_token_length": max_token_length,
    }


def render_summary(result: Dict[str, Any]) -> None:
    """
    Render the summary generated by the app.
    """
    title, selftext, output, prompts, summaries, groups = (
        result["title"],
        result["selftext"],
        result["output"],
        result["prompts"],
        result["summaries"],
        result["groups"],
    )

    save_output(str(title), str(output))

    st.text("Original Content:")
    st.subheader(title)
    st.text(selftext)

    for i, group in enumerate(groups):
        with st.expander(f"Group {i} length {num_tokens_from_string(group)} tokens"):
            st.code(group)

    st.subheader("Generated")
    for i, summary in enumerate(summaries):
        with st.expander(f"Prompt {i}"):
            st.code(prompts[i])
        st.subheader(f"OpenAI Completion Response: {i}")
        st.markdown(summary)


def render_layout(
    org_id: str,
    api_key: str,
    app_logger: Any = None,
    reddit_url: Optional[str] = None,
    selected_model: Optional[str] = None,
    settings: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Render the layout of the app.
    """

    st.header(APP_TITLE)
    st.subheader("by sean dearnaley")

    # Create an input box for url
    if reddit_url is None:
        reddit_url = render_input_box()
        if reddit_url is None:
            st.stop()

    if settings is None or selected_model is None:
        selected_model, settings = render_settings(org_id, api_key)

    # Create a button to submit the url
    if st.button("Generate it!"):
        summary_placeholder = st.empty()

        with summary_placeholder.container():
            with st.spinner("Wait for it..."):
                app_logger.info("Generating summary data")
                result = generate_summary_data(
                    settings["query_text"],
                    settings["chunk_token_length"],
                    settings["number_of_summaries"],
                    settings["max_token_length"],
                    replace_last_token_with_json(reddit_url),
                    selected_model,
                    org_id,
                    api_key,
                    app_logger,
                )

                if result is None:
                    st.error("No Summary Data")
                    st.stop()

                render_summary(result)
                app_logger.info("Summary data generated")
            st.success("Done!")

        if st.button("Clear"):
            summary_placeholder.empty()
