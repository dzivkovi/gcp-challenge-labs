"""
This module provides functionality to interact with Google Cloud's Vertex AI
and Streamlit for generating text responses using the Gemini model.
"""
import os
import logging
from google.cloud import logging as cloud_logging
import streamlit as st
import vertexai
from vertexai.preview.generative_models import (
    GenerationConfig,
    GenerativeModel,
    HarmBlockThreshold,
    HarmCategory,
)

# configure logging
logging.basicConfig(level=logging.INFO)
# attach a Cloud Logging handler to the root logger
log_client = cloud_logging.Client()
log_client.setup_logging()

PROJECT_ID = os.environ.get("GCP_PROJECT")  # Your Google Cloud Project ID
LOCATION = os.environ.get("GCP_REGION")  # Your Google Cloud Project Region
vertexai.init(project=PROJECT_ID, location=LOCATION)


@st.cache_resource
def load_models():
    """
    Load the Gemini model for generating text responses.

    Returns:
        GenerativeModel: The loaded Gemini model.
    """
    model = GenerativeModel("gemini-1.5-flash")
    return model


def get_gemini_pro_text_response(
    model: GenerativeModel,
    contents: str,  # pylint: disable=unused-argument
    generation_config: GenerationConfig,
    stream: bool = True,
):
    """
    Generate a text response using the Gemini model.

    Args:
        model (GenerativeModel): The Gemini model to use for generation.
        contents (str): The input text content for generation.

    Returns:
        str: The generated text response.

    """
    safety_settings = {
        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
        HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_ONLY_HIGH,
        HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
    }

    responses = model.generate_content(
        prompt,
        generation_config=generation_config,
        safety_settings=safety_settings,
        stream=stream,
    )

    final_response = []
    for res in responses:
        try:
            # st.write(res.text)
            final_response.append(res.text)
        except IndexError:
            # st.write(res)
            final_response.append("")
            continue
    return " ".join(final_response)


st.header("Vertex AI Gemini API", divider="gray")
text_model_pro = load_models()

st.write("Using Gemini Pro - Text only model")
st.subheader("AI Chef")

cuisine = st.selectbox(
    "What cuisine do you desire?",
    ("American", "Chinese", "French", "Indian", "Italian", "Japanese", "Mexican", "Turkish"),
    index=None,
    placeholder="Select your desired cuisine."
)

dietary_preference = st.selectbox(
    "Do you have any dietary preferences?",
    (
        "Diabetese",
        "Glueten free",
        "Halal",
        "Keto",
        "Kosher",
        "Lactose Intolerance",
        "Paleo",
        "Vegan",
        "Vegetarian",
        "None",
    ),
    index=None,
    placeholder="Select your desired dietary preference.",
)

allergy = st.text_input(
    "Enter your food allergy:  \n\n", key="allergy", value="peanuts"
)

ingredient_1 = st.text_input(
    "Enter your first ingredient:  \n\n", key="ingredient_1", value="ahi tuna"
)

ingredient_2 = st.text_input(
    "Enter your second ingredient:  \n\n", key="ingredient_2", value="chicken breast"
)

ingredient_3 = st.text_input(
    "Enter your third ingredient:  \n\n", key="ingredient_3", value="tofu"
)

# https://docs.streamlit.io/library/api-reference/widgets/st.radio
wine = st.radio(
    "Wine selection?",
    ("Red", "White", "None"),
)

MAX_OUTPUT_TOKENS = 2048

# Task 2.6
# Modify this prompt with the custom chef prompt.
prompt = f"""I am a Chef.  I need to create {cuisine} \n
recipes for customers who want {dietary_preference} meals. \n
However, don't include recipes that use ingredients with the customer's {allergy} allergy. \n
I have {ingredient_1}, \n
{ingredient_2}, \n
and {ingredient_3} \n
in my kitchen and other ingredients. \n
The customer's wine preference is {wine} \n
Please provide some for meal recommendations.
For each recommendation include preparation instructions,
time to prepare
and the recipe title at the begining of the response.
Then include the wine paring for each recommendation.
At the end of the recommendation provide the calories associated with the meal
and the nutritional facts.
"""

config = {
    "temperature": 0.8,
    "max_output_tokens": MAX_OUTPUT_TOKENS,
}

generate_t2t = st.button("Generate my recipes.", key="generate_t2t")
if generate_t2t and prompt:
    # st.write(prompt)
    with st.spinner("Generating your recipes using Gemini..."):
        first_tab1, first_tab2 = st.tabs(["Recipes", "Prompt"])
        with first_tab1:
            llm_response = get_gemini_pro_text_response(    # pylint: disable=invalid-name
                text_model_pro,
                prompt,
                generation_config=config,
            )
            if llm_response:
                st.write("Your recipes:")
                st.write(llm_response)
                logging.info(llm_response)
        with first_tab2:
            st.text(prompt)
