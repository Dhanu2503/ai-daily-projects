import streamlit as st
from PIL import Image
import numpy as np
import tensorflow as tf
from tensorflow.keras.applications.mobilenet_v2 import MobileNetV2, preprocess_input, decode_predictions
import io
import requests

# --- Configuration ---
MODEL_IMAGE_SIZE = (224, 224)

# Detailed mapping for specific ImageNet classes and generic categories
WASTE_CATEGORIES_INFO = {
    # Specific ImageNet class mappings
    'water bottle': {'category': 'Plastic', 'disposal': 'Rinse and recycle in plastic bin. Check local codes.'},
    'plastic bag': {'category': 'Plastic', 'disposal': 'Often not recycled curbside. Return to store or check local guidelines.'},
    'soda can': {'category': 'Metal', 'disposal': 'Rinse and recycle in metal/aluminum bin.'},
    'beer bottle': {'category': 'Glass', 'disposal': 'Rinse and recycle in glass bin.'},
    'wine bottle': {'category': 'Glass', 'disposal': 'Rinse and recycle in glass bin.'},
    'banana': {'category': 'Organic', 'disposal': 'Compost if possible, otherwise dispose in organic waste.'},
    'apple': {'category': 'Organic', 'disposal': 'Compost if possible, otherwise dispose in organic waste.'},
    'orange': {'category': 'Organic', 'disposal': 'Compost if possible, otherwise dispose in organic waste.'},
    'newspaper': {'category': 'Paper', 'disposal': 'Recycle in paper/cardboard bin.'},
    'book': {'category': 'Paper', 'disposal': 'Recycle in paper/cardboard bin. Remove hardcovers if present.'},
    'cardboard box': {'category': 'Paper', 'disposal': 'Flatten and recycle in paper/cardboard bin.'},
    'remote control': {'category': 'E-waste', 'disposal': 'Do not put in regular trash. Take to an e-waste collection point.'},
    'computer keyboard': {'category': 'E-waste', 'disposal': 'Do not put in regular trash. Take to an e-waste collection point.'},
    'cellular telephone': {'category': 'E-waste', 'disposal': 'Do not put in regular trash. Take to an e-waste collection point.'},
    'monitor': {'category': 'E-waste', 'disposal': 'Do not put in regular trash. Take to an e-waste collection point.'},

    # Generic category definitions with default advice
    'Plastic': {'category': 'Plastic', 'disposal': 'Recycle in plastic bin. Ensure items are clean and dry.'},
    'Metal': {'category': 'Metal', 'disposal': 'Recycle in metal/aluminum bin. Ensure items are clean and dry.'},
    'Glass': {'category': 'Glass', 'disposal': 'Recycle in glass bin. Ensure items are clean and dry.'},
    'Paper': {'category': 'Paper', 'disposal': 'Recycle in paper/cardboard bin. Flatten boxes and remove non-paper elements.'},
    'Organic': {'category': 'Organic', 'disposal': 'Compost if possible, otherwise dispose in organic waste.'},
    'E-waste': {'category': 'E-waste', 'disposal': 'Special disposal required. Take to an e-waste collection point.'},
    'Textile': {'category': 'Textile', 'disposal': 'Donate if usable, otherwise check textile recycling programs.'},
    'General Waste': {'category': 'General Waste', 'disposal': 'Dispose in regular landfill waste.'},
    'Uncertain': {'category': 'Uncertain', 'disposal': 'Cannot determine category. Please check local guidelines for proper disposal.'}
}

# Keyword-based mapping for general categories (if no specific ImageNet class matches)
DEFAULT_WASTE_KEYWORD_MAPPING = {
    'bottle': 'Plastic',
    'cup': 'Plastic',
    'can': 'Metal',
    'fruit': 'Organic',
    'vegetable': 'Organic',
    'paper': 'Paper',
    'box': 'Paper',
    'glass': 'Glass',
    'electronic': 'E-waste',
    'container': 'Plastic',
    'bag': 'Plastic',
    'food': 'Organic',
    'waste': 'General Waste',
    'trash': 'General Waste',
    'dirt': 'Organic',
    'leaf': 'Organic',
    'branch': 'Organic',
    'stone': 'General Waste',
    'rock': 'General Waste',
    'tool': 'Metal',
    'utensil': 'Metal',
    'toy': 'Plastic',
    'clothing': 'Textile',
    'shoe': 'Textile',
    'fabric': 'Textile',
    'rubber': 'General Waste',
    'metal': 'Metal',
    'plastic': 'Plastic',
    'wood': 'Organic',
    'ceramic': 'General Waste',
    'tile': 'General Waste',
    'brick': 'General Waste',
    'material': 'General Waste' # Catch-all for unknown materials
}

# --- Model Loading ---
@st.cache_resource
def load_model():
    """Loads the pre-trained MobileNetV2 model."""
    try:
        model = MobileNetV2(weights='imagenet')
        return model
    except Exception as e:
        st.error(f"Error loading model: {e}. Please ensure you have an internet connection to download weights.")
        st.stop()

model = load_model()

# --- Prediction Functions ---
def preprocess_image(image: Image.Image) -> np.ndarray:
    """
    Preprocesses the uploaded image for the MobileNetV2 model.
    Resizes, converts to array, expands dimensions, and applies MobileNetV2-specific preprocessing.
    """
    image = image.resize(MODEL_IMAGE_SIZE)
    image_array = np.asarray(image)
    if image_array.shape[2] == 4:  # Convert RGBA to RGB if necessary
        image_array = image_array[:, :, :3]
    image_array = np.expand_dims(image_array, axis=0)
    image_array = preprocess_input(image_array)
    return image_array

def predict_waste_category(image: Image.Image) -> tuple:
    """
    Predicts the waste category and provides disposal information.
    Uses MobileNetV2 to get top ImageNet predictions and then maps them.
    """
    processed_image = preprocess_image(image)
    predictions = model.predict(processed_image)
    decoded_predictions = decode_predictions(predictions, top=5)[0] # Get top 5 ImageNet predictions

    best_match_info = WASTE_CATEGORIES_INFO['Uncertain']
    best_confidence = 0.0

    # First pass: Try to find an explicit exact mapping from WASTE_CATEGORIES_INFO
    for _, imgnet_class, confidence in decoded_predictions:
        if imgnet_class in WASTE_CATEGORIES_INFO:
            if confidence > best_confidence:
                best_match_info = WASTE_CATEGORIES_INFO[imgnet_class]
                best_confidence = confidence
            # For exact matches, we prioritize the highest confidence one, but don't break yet
            # in case a lower-ranked prediction has higher confidence (unlikely for top-K, but robust)

    if best_match_info['category'] != 'Uncertain':
        return best_match_info, best_confidence # Return if an explicit match was found

    # Second pass: If no explicit match, try to infer from keywords
    # Iterate through predictions again to find keyword matches
    for _, imgnet_class, confidence in decoded_predictions:
        for keyword, category_name in DEFAULT_WASTE_KEYWORD_MAPPING.items():
            if keyword in imgnet_class.lower():
                # Get the detailed info for this general category
                info = WASTE_CATEGORIES_INFO.get(category_name, {'category': category_name, 'disposal': f'Likely {category_name}. Please verify local recycling rules.'})
                if confidence > best_confidence:
                    best_match_info = info
                    best_confidence = confidence
                break # Found a keyword match for this imgnet_class, move to next imgnet_class
        if best_match_info['category'] != 'Uncertain': # If a keyword match was found
            break # Stop checking other ImageNet classes if we've found a suitable category

    return best_match_info, best_confidence


# --- Streamlit UI ---
st.set_page_config(
    page_title="EcoSort AI: Smart Waste Classifier",
    page_icon="♻️",
    layout="centered",
    initial_sidebar_state="expanded"
)

st.title("♻️ EcoSort AI: Smart Waste Classifier")
st.markdown(
    """
    Upload an image of your waste item, and EcoSort AI will attempt to classify it
    and provide guidance on how to dispose of it responsibly.

    **Note:** This is a demonstration using a general image classification model
    (MobileNetV2) with a simulated mapping to waste categories. For real-world
    applications, a model specifically trained on waste datasets would be required.
    """
)

# File uploader
uploaded_file = st.file_uploader("Choose an image...", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    # Display uploaded image
    image = Image.open(uploaded_file)
    st.image(image, caption='Uploaded Waste Item', use_column_width=True)
    st.write("")

    if st.button("Classify Waste"): # Add a key to prevent rerun warnings if using multiple buttons
        with st.spinner('Classifying...'):
            classification_result, confidence = predict_waste_category(image)

            st.subheader("Classification Result:")
            st.write(f"**Predicted Category:** {classification_result['category']}")
            st.write(f"**Confidence:** {confidence:.2f}") # This confidence is from ImageNet top prediction
            st.info(f"**Disposal Advice:** {classification_result['disposal']}")

            if classification_result['category'] in ['Plastic', 'Paper', 'Metal', 'Glass']:
                st.success("Great! This item is likely recyclable. Remember to clean items before recycling!")
            elif classification_result['category'] == 'Organic':
                st.success("This item is organic. Consider composting if possible!")
            elif classification_result['category'] == 'E-waste':
                st.warning("This is E-waste. It requires special disposal! Do not put in regular trash.")
            elif classification_result['category'] == 'General Waste' or classification_result['category'] == 'Uncertain':
                st.error("This item might be general waste or its category is uncertain. Please double-check local guidelines.")

st.sidebar.header("About EcoSort AI")
st.sidebar.markdown(
    """
    EcoSort AI aims to assist in proper waste segregation by leveraging AI.
    By identifying waste types, we can promote better recycling habits and
    reduce landfill waste.

    This prototype uses a pre-trained general object recognition model
    and a custom rule-based mapping for demonstration purposes.
    """
)
st.sidebar.markdown("--- ---")
st.sidebar.write("Developed by EcoTech Solutions")

# Optional: Add a section for example images
st.markdown("--- ---")
st.subheader("Try with Example Images:")

example_images = {
    "Plastic Bottle": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/10/Plastic_PET_bottle_%28water_bottle%29.jpg/256px-Plastic_PET_bottle_%28water_bottle%29.jpg",
    "Banana Peel": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c2/Banana_peel_on_concrete.jpg/256px-Banana_peel_on_concrete.jpg",
    "Aluminum Can": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/91/Drink_can_open_cropped.png/256px-Drink_can_open_cropped.png",
    "Newspaper": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c9/Newspaper_Folding.jpg/256px-Newspaper_Folding.jpg"
}

cols = st.columns(len(example_images))
for i, (name, url) in enumerate(example_images.items()):
    with cols[i]:
        st.image(url, caption=name, width=100)
        if st.button(f"Try {name}", key=f"example_btn_{i}"):
            try:
                response = requests.get(url)
                if response.status_code == 200:
                    image = Image.open(io.BytesIO(response.content))
                    st.image(image, caption=f'Example: {name}', use_column_width=True)
                    with st.spinner(f'Classifying example: {name}...'):
                        classification_result, confidence = predict_waste_category(image)
                        st.subheader("Classification Result:")
                        st.write(f"**Predicted Category:** {classification_result['category']}")
                        st.write(f"**Confidence:** {confidence:.2f}")
                        st.info(f"**Disposal Advice:** {classification_result['disposal']}")
                else:
                    st.error(f"Could not fetch example image: {name}")
            except Exception as e:
                st.error(f"Error processing example image: {e}")
