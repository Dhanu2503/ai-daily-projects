import streamlit as st
import os
from openai import OpenAI
import json
import random

# --- Configuration ---
# It's recommended to set OPENAI_API_KEY as an environment variable
# or use Streamlit secrets for deployment (e.g., in .streamlit/secrets.toml).
# For local testing, ensure your API key is in your environment variables.
try:
    openai_api_key = os.environ.get("OPENAI_API_KEY") or st.secrets["OPENAI_API_KEY"]
except KeyError:
    st.error("OpenAI API key not found. Please set the OPENAI_API_KEY environment variable or configure it in Streamlit secrets.")
    st.stop()

client = OpenAI(api_key=openai_api_key)

# --- Persona Elements and Archetypes ---
GENRE_OPTIONS = [
    "Fantasy", "Sci-Fi", "Mystery", "Thriller", "Horror", "Romance",
    "Historical Fiction", "Contemporary", "Dystopian", "Post-Apocalyptic",
    "Cyberpunk", "Steampunk", "Urban Fantasy", "Mythology", "Adventure",
    "Literary Fiction", "Young Adult", "Children's Story", "Slice of Life"
]

COMPLEXITY_LEVELS = {
    "Simple (Basic Traits)": 0.5,
    "Moderate (Detailed Backstory)": 1.0,
    "Complex (Deep Psychology, Conflict)": 1.5,
    "Epic (Interconnected, World-Impacting)": 2.0
}

def generate_persona_prompt(core_idea, genre, complexity_factor):
    # Base mandatory elements for any persona
    elements_to_request = [
        ("name", "Full Name"),
        ("age", "Age (e.g., 20s, ancient, ageless)"),
        ("gender", "Gender identity (e.g., Male, Female, Non-binary, Fluid)"),
        ("occupation", "What they do for a living or their primary role"),
        ("personality_traits", "List of 3-5 core personality traits (e.g., Brave, Cynical, Loyal)"),
        ("motivations", "List of 3-5 things that drive them (e.g., Revenge, Love, Power, Justice)"),
        ("backstory_summary", "A concise 2-3 sentence summary of their past that shaped them."),
        ("quirks", "List of 2-3 unique habits, mannerisms, or oddities"),
        ("goals", "List of 2-3 primary objectives or aspirations"),
        ("conflicts", "List of 2-3 internal or external struggles they face"),
        ("appearance", "A vivid 2-3 sentence description of their physical look")
    ]
    
    # Add more complex elements based on complexity_factor
    if complexity_factor >= 1.0: # Moderate and above
        elements_to_request.extend([
            ("voice_style", "How they speak (e.g., raspy, articulate, shy, booming)"),
            ("secret", "A hidden truth or vulnerability (1-2 sentences)"),
            ("relationship_dynamics", "List of 2-3 ways they interact with others (e.g., Distrustful of authority, Protective of loved ones)")
        ])
    if complexity_factor >= 1.5: # Complex and above
        elements_to_request.extend([
            ("fatal_flaw", "Their most significant character weakness (1 sentence)"),
            ("strengths", "List of 2-3 key abilities or virtues")
        ])

    # Format the requested elements into a string for the prompt
    json_description = "\n".join([f'- "{key}": {desc}' for key, desc in elements_to_request])

    prompt = f"""
    You are an AI Muse, an expert at creating dynamic and complex fictional characters.
    Generate a detailed persona based on the following creative brief.
    The persona should be suitable for a story with the core idea/theme: "{core_idea}".
    The genre/setting is: "{genre}".

    Provide the persona details as a JSON object with the following keys.
    For list items, provide 3-5 distinct elements unless specified otherwise.
    Ensure all string values are concise and compelling.

    Requested JSON Keys and their descriptions (fill these in):
    {json_description}

    Begin JSON output:
    """
    
    return prompt

def get_ai_persona(core_idea, genre, complexity_factor):
    prompt_text = generate_persona_prompt(core_idea, genre, complexity_factor)
    
    try:
        with st.spinner("Generating persona... This might take a moment."):
            response = client.chat.completions.create(
                model="gpt-4o", # Consider "gpt-3.5-turbo" for faster, cheaper results (less creative)
                messages=[
                    {"role": "system", "content": "You are a creative writing assistant that generates dynamic character personas in JSON format."},
                    {"role": "user", "content": prompt_text}
                ],
                response_format={"type": "json_object"}, # Instruct the model to return JSON
                temperature=0.7 + (complexity_factor * 0.1) # Higher temperature for more creativity
            )
            
            persona_json_str = response.choices[0].message.content
            persona_data = json.loads(persona_json_str)
            return persona_data
    except json.JSONDecodeError:
        st.error("Failed to parse the AI's response as JSON. This might indicate an issue with the AI's output or the prompt. Please try again.")
        st.error(f"Raw AI response (debug): {persona_json_str[:500]}...") # Show part of the response for debugging
        return None
    except Exception as e:
        st.error(f"An error occurred during AI persona generation: {e}")
        return None

# --- Streamlit UI ---
st.set_page_config(
    page_title="The AI Muse: Dynamic Persona Generator",
    page_icon="🎭",
    layout="wide"
)

st.title("🎭 The AI Muse: Dynamic Persona Generator")
st.markdown("""
    Unleash your creativity with an AI-powered tool designed to craft unique and detailed character personas for your stories, games, or role-playing scenarios.
    Provide a core idea, select a genre, and let the muse inspire you!
""")

with st.sidebar:
    st.header("Generate Your Persona")
    core_idea = st.text_area(
        "Core Idea / Story Premise",
        "A detective haunted by a past case uncovers a conspiracy in a technologically advanced city.",
        help="Provide the central theme, plot, or character concept for your story."
    )
    
    genre = st.selectbox(
        "Genre / Setting",
        GENRE_OPTIONS,
        index=GENRE_OPTIONS.index("Mystery"),
        help="Choose the literary genre or primary setting for the persona."
    )

    complexity_choice = st.select_slider(
        "Detail & Complexity Level",
        options=list(COMPLEXITY_LEVELS.keys()),
        value="Moderate (Detailed Backstory)",
        help="Adjust for more basic traits or a deeply intricate character with psychology and conflict."
    )
    complexity_factor = COMPLEXITY_LEVELS[complexity_choice]

    st.markdown("--- Expansion Ideas ---")
    st.write("### Advanced Options (Future Features)")
    st.checkbox("Iterative Refinement", disabled=True, help="Allow editing and re-generating specific parts of the persona.")
    st.checkbox("Generate Multiple Personas", disabled=True, help="Generate 3 distinct personas for comparison.")
    
    generate_button = st.button("Generate Persona", type="primary")

st.markdown("--- Summary ---")

if generate_button:
    if not openai_api_key:
        st.error("OpenAI API key is missing. Please set it in your environment or Streamlit secrets.")
    elif not core_idea.strip():
        st.warning("Please provide a 'Core Idea / Story Premise' to generate a persona.")
    else:
        persona = get_ai_persona(core_idea, genre, complexity_factor)
        
        if persona:
            st.subheader("✨ Your Generated Persona ✨")
            
            col1, col2 = st.columns([1, 2])
            with col1:
                # Generate a random number to bust cache for new image on refresh
                st.image("https://loremflickr.com/320/320/person,face?random=" + str(random.randint(0,1000)), caption="Placeholder Image", use_column_width=True)
            with col2:
                st.markdown(f"## {persona.get('name', 'N/A')}")
                st.markdown(f"**Age:** {persona.get('age', 'N/A')}")
                st.markdown(f"**Gender:** {persona.get('gender', 'N/A')}")
                st.markdown(f"**Occupation:** {persona.get('occupation', 'N/A')}")
            
            st.markdown("--- Traits ---")
            
            st.subheader("Core Identity")
            st.markdown(f"**Personality Traits:** {', '.join(persona.get('personality_traits', ['N/A']))}")
            st.markdown(f"**Motivations:** {', '.join(persona.get('motivations', ['N/A']))}")
            st.markdown(f"**Goals:** {', '.join(persona.get('goals', ['N/A']))}")
            st.markdown(f"**Conflicts:** {', '.join(persona.get('conflicts', ['N/A']))}")

            st.subheader("Backstory & Lore")
            st.markdown(f"**Backstory Summary:** {persona.get('backstory_summary', 'N/A')}")
            
            if "secret" in persona and complexity_factor >= 1.0:
                st.markdown(f"**Secret:** {persona.get('secret', 'N/A')}")

            st.subheader("Distinctive Features")
            st.markdown(f"**Appearance:** {persona.get('appearance', 'N/A')}")
            st.markdown(f"**Quirks:** {', '.join(persona.get('quirks', ['N/A']))}")
            
            if "voice_style" in persona and complexity_factor >= 1.0:
                st.markdown(f"**Voice Style:** {persona.get('voice_style', 'N/A')}")
            
            if "relationship_dynamics" in persona and complexity_factor >= 1.0:
                st.markdown(f"**Relationship Dynamics:** {', '.join(persona.get('relationship_dynamics', ['N/A']))}")

            # Only show this subheader if at least one of these complex elements is present
            if ("strengths" in persona and complexity_factor >= 1.5) or \
               ("fatal_flaw" in persona and complexity_factor >= 1.5):
                st.subheader("Strengths & Flaws")
                if "strengths" in persona and complexity_factor >= 1.5:
                    st.markdown(f"**Strengths:** {', '.join(persona.get('strengths', ['N/A']))}")
                if "fatal_flaw" in persona and complexity_factor >= 1.5:
                    st.markdown(f"**Fatal Flaw:** {persona.get('fatal_flaw', 'N/A')}")

            st.markdown("--- Actions ---")
            st.download_button(
                label="Download Persona as JSON",
                data=json.dumps(persona, indent=2),
                file_name=f"{persona.get('name', 'generated_persona').replace(' ', '_').lower()}.json",
                mime="application/json"
            )

st.markdown("---")
st.info("💡 **Tip:** Adjust the 'Detail & Complexity Level' to get more elaborate personas. Higher complexity means more unique attributes.")
