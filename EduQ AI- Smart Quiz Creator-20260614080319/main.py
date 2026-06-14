import streamlit as st
import openai
import json
import os
import io

# --- Configuration ---
# Set your OpenAI API key here.
# It's recommended to set this as an environment variable for production.
# Example: export OPENAI_API_KEY='your_api_key_here'
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    st.error("OpenAI API key not found. Please set the OPENAI_API_KEY environment variable.")
    st.stop() # Stop the app if API key is not available

openai.api_key = OPENAI_API_KEY

# --- LLM Interaction Function ---
def generate_quiz_content(topic: str, difficulty: str, num_questions: int, q_types: list) -> list:
    """
    Generates quiz questions using the OpenAI GPT model.
    """
    q_types_str = ", ".join(q_types)
    
    # The detailed prompt guides the AI to produce structured JSON output
    prompt = f"""
    You are an intelligent quiz creator.
    Generate a quiz on the topic: "{topic}".
    Difficulty: "{difficulty}".
    Number of questions: {num_questions}.
    Question types requested: {q_types_str}.

    Format the output as a JSON array of question objects.
    Each question object should have the following keys:
    - "question": The question text.
    - "type": "multiple_choice", "true_false", or "short_answer".
    - "difficulty": "Easy", "Medium", or "Hard".
    - "options" (only for multiple_choice): An array of strings representing answer choices.
    - "correct_answer" (for multiple_choice and true_false): The correct option or "True"/"False".
    - "answer" (for short_answer): The expected short answer.
    - "explanation": A brief explanation for the correct answer.

    Ensure the response is a valid JSON array. Do not include any introductory or concluding text outside the JSON.
    
    Example for multiple choice:
    {{
        "question": "What is the capital of France?",
        "type": "multiple_choice",
        "difficulty": "Easy",
        "options": ["Berlin", "Madrid", "Paris", "Rome"],
        "correct_answer": "Paris",
        "explanation": "Paris is the capital and most populous city of France."
    }}

    Example for true/false:
    {{
        "question": "The Earth is flat.",
        "type": "true_false",
        "difficulty": "Easy",
        "correct_answer": "False",
        "explanation": "The Earth is an oblate spheroid."
    }}

    Example for short answer:
    {{
        "question": "What is the chemical symbol for water?",
        "type": "short_answer",
        "difficulty": "Easy",
        "answer": "H2O",
        "explanation": "Water is a chemical compound with the chemical formula H2O."
    }}
    """

    messages = [
        {"role": "system", "content": "You are a helpful assistant specialized in generating quizzes in JSON format."},
        {"role": "user", "content": prompt}
    ]

    try:
        # Call OpenAI API
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo-0125", # Or other models like gpt-4-turbo-preview
            messages=messages,
            response_format={"type": "json_object"}, # Crucial for instructing GPT to return JSON
            temperature=0.7,
            max_tokens=2048 # Adjust based on expected output size
        )
        
        content = response.choices[0].message.content
        quiz_data = json.loads(content) # Parse the JSON response
        return quiz_data
    except json.JSONDecodeError as e:
        st.error(f"Failed to decode JSON from API response. Error: {e}")
        st.code(content) # Show the raw response for debugging
        return []
    except openai.APIError as e:
        st.error(f"OpenAI API error: {e}")
        return []
    except Exception as e:
        st.error(f"An unexpected error occurred: {e}")
        return []

# --- Streamlit UI ---
st.set_page_config(
    page_title="EduQ AI: Smart Quiz Creator",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🧠 EduQ AI: Smart Quiz Creator")
st.markdown("""
Welcome to EduQ AI! Easily generate custom quizzes on any topic using the power of AI.
Just provide a topic, choose difficulty and question types, and let AI do the rest.
""")

st.sidebar.header("Quiz Settings")
with st.sidebar:
    topic = st.text_input("Enter Topic", "Python Programming")
    difficulty = st.selectbox("Difficulty", ["Easy", "Medium", "Hard"], index=1)
    num_questions = st.slider("Number of Questions", 1, 15, 5)
    question_types = st.multiselect(
        "Question Types",
        ["Multiple Choice", "True/False", "Short Answer"],
        ["Multiple Choice", "True/False"]
    )

    generate_button = st.button("Generate Quiz!", use_container_width=True, type="primary")

# --- Quiz Generation and Display ---
# Use session state to preserve quiz data across reruns
if 'quiz_generated' not in st.session_state:
    st.session_state.quiz_generated = False
if 'generated_quiz_data' not in st.session_state:
    st.session_state.generated_quiz_data = []

if generate_button:
    if not topic:
        st.error("Please enter a topic to generate a quiz.")
    elif not question_types:
        st.error("Please select at least one question type.")
    else:
        with st.spinner("Generating your smart quiz... This might take a moment."):
            quiz_data = generate_quiz_content(topic, difficulty, num_questions, question_types)
            if quiz_data:
                st.session_state.generated_quiz_data = quiz_data
                st.session_state.quiz_generated = True
                st.success("Quiz generated successfully!")
            else:
                st.session_state.quiz_generated = False
                st.error("Could not generate quiz. Please check logs for details or try again.")

# Display the generated quiz if available
if st.session_state.quiz_generated and st.session_state.generated_quiz_data:
    st.header(f"Generated Quiz: {topic} ({difficulty})")

    # Options to download/view raw quiz data
    col1, col2, col3 = st.columns([1,1,2])
    with col1:
        json_string = json.dumps(st.session_state.generated_quiz_data, indent=2)
        st.download_button(
            label="Download JSON",
            data=json_string,
            file_name=f"{topic.replace(' ', '_')}_quiz.json",
            mime="application/json",
            use_container_width=True
        )
    with col2:
        # Create a simple text format for download
        text_quiz = io.StringIO()
        for i, q in enumerate(st.session_state.generated_quiz_data):
            text_quiz.write(f"Q{i+1}: {q.get('question', 'N/A')}\n")
            if q.get('type') == 'multiple_choice' and 'options' in q and isinstance(q['options'], list):
                for j, option in enumerate(q['options']):
                    text_quiz.write(f"  {chr(65+j)}. {option}\n")
            elif q.get('type') == 'true_false':
                text_quiz.write("  (True/False)\n")
            
            correct_info = q.get('correct_answer', q.get('answer', 'N/A'))
            text_quiz.write(f"  Correct Answer: {correct_info}\n")
            text_quiz.write(f"  Explanation: {q.get('explanation', 'No explanation provided.')}\n")
            text_quiz.write("\n---\n\n")

        st.download_button(
            label="Download TXT",
            data=text_quiz.getvalue(),
            file_name=f"{topic.replace(' ', '_')}_quiz.txt",
            mime="text/plain",
            use_container_width=True
        )
    with col3:
        if st.checkbox("Show Raw JSON Output"): # Option to view the raw JSON from AI
            st.json(st.session_state.generated_quiz_data)

    # Display each question in a user-friendly format
    for i, q in enumerate(st.session_state.generated_quiz_data):
        st.subheader(f"Question {i+1}: {q.get('question', 'N/A')}")
        st.markdown(f"**Type**: {q.get('type', 'N/A').replace('_', ' ').title()} | **Difficulty**: {q.get('difficulty', 'N/A')}")

        if q.get('type') == 'multiple_choice':
            if 'options' in q and isinstance(q['options'], list):
                for j, option in enumerate(q['options']):
                    st.markdown(f"- **{chr(65+j)}. {option}**")
            else:
                st.warning("Multiple choice question missing 'options'.")
            st.info(f"Correct Answer: {q.get('correct_answer', 'N/A')}")
        elif q.get('type') == 'true_false':
            st.info(f"Correct Answer: {q.get('correct_answer', 'N/A')}")
        elif q.get('type') == 'short_answer':
            st.info(f"Expected Answer: {q.get('answer', 'N/A')}")
        
        # Provide an expandable explanation for each question
        if 'explanation' in q and q['explanation']:
            with st.expander("Show Explanation"):
                st.markdown(q['explanation'])
        st.markdown("---")

st.markdown("""
---
**How to Run This App:**
1. Save the code above as `main.py`.
2. Create a `requirements.txt` file (see below).
3. Install dependencies: `pip install -r requirements.txt`.
4. Set your OpenAI API key as an environment variable: `export OPENAI_API_KEY='your_api_key_here'` (Linux/macOS) or `$env:OPENAI_API_KEY='your_api_key_here'` (Windows PowerShell).
5. Run the app: `streamlit run main.py` in your terminal.
""")
