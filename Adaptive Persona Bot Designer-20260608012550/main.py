import json
import os
import time

class Persona:
    """Represents a chatbot persona with various attributes."""
    def __init__(self, name, role, background, tone, communication_style,
                 core_values, common_phrases, knowledge_domains, goals):
        self.name = name
        self.role = role
        self.background = background
        self.tone = tone
        self.communication_style = communication_style
        self.core_values = core_values
        self.common_phrases = common_phrases
        self.knowledge_domains = knowledge_domains
        self.goals = goals

    def to_dict(self):
        return {
            "name": self.name,
            "role": self.role,
            "background": self.background,
            "tone": self.tone,
            "communication_style": self.communication_style,
            "core_values": self.core_values,
            "common_phrases": self.common_phrases,
            "knowledge_domains": self.knowledge_domains,
            "goals": self.goals
        }

    @classmethod
    def from_dict(cls, data):
        return cls(**data)

    def display(self):
        print("\n--- Persona Details ---")
        for key, value in self.to_dict().items():
            print(f"- {key.replace('_', ' ').title()}: {value}")
        print("-----------------------")

    def get_summary(self):
        return f"{self.name} - A {self.tone} {self.role} bot. Core values: {', '.join(self.core_values)}."


class PersonaDesigner:
    """Manages the creation, editing, and evaluation of personas."""
    def __init__(self, personas_dir="personas"):
        self.personas_dir = personas_dir
        os.makedirs(self.personas_dir, exist_ok=True)
        self.personas = self._load_personas()

    def _load_personas(self):
        personas = {}
        for filename in os.listdir(self.personas_dir):
            if filename.endswith(".json"):
                filepath = os.path.join(self.personas_dir, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        persona = Persona.from_dict(data)
                        personas[persona.name] = persona
                except json.JSONDecodeError:
                    print(f"Warning: Could not decode JSON from {filename}. Skipping.")
                except Exception as e:
                    print(f"Error loading {filename}: {e}")
        return personas

    def _save_persona(self, persona):
        filepath = os.path.join(self.personas_dir, f"{persona.name}.json")
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(persona.to_dict(), f, indent=4)
        self.personas[persona.name] = persona
        print(f"Persona '{persona.name}' saved successfully.")

    def list_personas(self):
        if not self.personas:
            print("No personas designed yet.")
            return
        print("\n--- Existing Personas ---")
        for i, (name, persona) in enumerate(self.personas.items()):
            print(f"{i+1}. {persona.get_summary()}")
        print("-------------------------")

    def get_persona_choice(self):
        self.list_personas()
        if not self.personas:
            return None
        while True:
            choice = input("Enter the number of the persona to select, or 'b' to go back: ").strip()
            if choice.lower() == 'b':
                return None
            try:
                index = int(choice) - 1
                if 0 <= index < len(self.personas):
                    selected_name = list(self.personas.keys())[index]
                    return self.personas[selected_name]
                else:
                    print("Invalid number. Please try again.")
            except ValueError:
                print("Invalid input. Please enter a number or 'b'.")

    def _get_input_guided(self, prompt, examples, is_list=False):
        print(f"\n{prompt}")
        print(f"Examples: {examples}")
        if is_list:
            print("Enter items separated by commas, or 'N/A' if not applicable.")
        user_input = input("> ").strip()
        if user_input.lower() == 'n/a' and is_list:
            return []
        if is_list:
            return [item.strip() for item in user_input.split(',') if item.strip()]
        return user_input

    def create_persona_guided(self):
        print("\n--- Design Your New Persona ---")
        while True:
            name = input("Enter a unique name for this persona: ").strip()
            if not name:
                print("Persona name cannot be empty.")
            elif name in self.personas:
                print(f"A persona named '{name}' already exists. Please choose a different name.")
            else:
                break

        role = self._get_input_guided(
            "What is the bot's primary role or function?",
            "e.g., 'Customer Support Agent', 'Creative Writing Assistant', 'Technical Troubleshooter'"
        )
        background = self._get_input_guided(
            "Provide a brief background story or context for this bot.",
            "e.g., 'An AI developed to assist users with Python programming challenges.', 'A digital librarian focused on ancient history.'"
        )
        tone = self._get_input_guided(
            "What is the bot's predominant tone of voice?",
            "e.g., 'formal', 'friendly and enthusiastic', 'empathetic', 'sarcastic', 'neutral and factual'"
        )
        communication_style = self._get_input_guided(
            "Describe the bot's communication style.",
            "e.g., 'concise and direct', 'verbose with detailed explanations', 'uses emojis frequently', 'asks clarifying questions'"
        )
        core_values = self._get_input_guided(
            "What are the core principles or values that guide this bot's responses?",
            "e.g., 'helpfulness', 'efficiency', 'empathy', 'factual accuracy', 'user privacy'",
            is_list=True
        )
        common_phrases = self._get_input_guided(
            "List any common phrases, greetings, or sign-offs the bot should use.",
            "e.g., 'Hello there!', 'How can I assist you today?', 'Happy to help!', 'Thank you for chatting!'",
            is_list=True
        )
        knowledge_domains = self._get_input_guided(
            "What are the primary areas of knowledge or topics this bot is proficient in?",
            "e.g., 'Python programming', 'World history', 'Product specifications for XYZ Inc.', 'Healthy cooking recipes'",
            is_list=True
        )
        goals = self._get_input_guided(
            "What are the main objectives this bot aims to achieve?",
            "e.g., 'Resolve user issues efficiently', 'Educate users on a topic', 'Entertain and engage users', 'Gather feedback'",
            is_list=True
        )

        new_persona = Persona(name, role, background, tone, communication_style,
                              core_values, common_phrases, knowledge_domains, goals)
        new_persona.display()
        confirm = input("Looks good? (y/n): ").strip().lower()
        if confirm == 'y':
            self._save_persona(new_persona)
            print(f"Persona '{name}' created and saved!")
        else:
            print("Persona creation cancelled.")

    def edit_persona_guided(self, persona_to_edit):
        print(f"\n--- Editing Persona: {persona_to_edit.name} ---")
        persona_to_edit.display()

        attributes = {
            "1": ("role", "What is the bot's primary role or function?", "e.g., 'Customer Support Agent', 'Creative Writing Assistant'"),
            "2": ("background", "Provide a brief background story or context for this bot.", "e.g., 'An AI developed to assist users with Python programming challenges.'"),
            "3": ("tone", "What is the bot's predominant tone of voice?", "e.g., 'formal', 'friendly and enthusiastic', 'empathetic'"),
            "4": ("communication_style", "Describe the bot's communication style.", "e.g., 'concise and direct', 'uses emojis frequently'"),
            "5": ("core_values", "What are the core principles or values that guide this bot's responses?", "e.g., 'helpfulness', 'efficiency', 'empathy'", True),
            "6": ("common_phrases", "List any common phrases, greetings, or sign-offs the bot should use.", "e.g., 'Hello there!', 'How can I assist you today?'", True),
            "7": ("knowledge_domains", "What are the primary areas of knowledge or topics this bot is proficient in?", "e.g., 'Python programming', 'World history'", True),
            "8": ("goals", "What are the main objectives this bot aims to achieve?", "e.g., 'Resolve user issues efficiently', 'Educate users on a topic'", True)
        }

        while True:
            print("\nSelect an attribute to edit:")
            for key, (attr_name, _, _, *_) in attributes.items():
                print(f"{key}. {attr_name.replace('_', ' ').title()} (Current: {getattr(persona_to_edit, attr_name)})")
            print("b. Back to main menu")

            choice = input("Enter your choice: ").strip().lower()
            if choice == 'b':
                break

            if choice in attributes:
                attr_key, prompt, examples, *is_list_arg = attributes[choice]
                is_list = is_list_arg[0] if is_list_arg else False
                new_value = self._get_input_guided(prompt, examples, is_list)
                setattr(persona_to_edit, attr_key, new_value)
                print(f"'{attr_key.replace('_', ' ').title()}' updated.")
                self._save_persona(persona_to_edit) # Save after each attribute edit
                persona_to_edit.display()
            else:
                print("Invalid choice. Please try again.")

    def evaluate_persona(self, persona_to_evaluate):
        print(f"\n--- Evaluating Persona: {persona_to_evaluate.name} ---")
        print("Please consider the following questions to evaluate the persona's effectiveness:")

        questions = [
            "1. Is the persona's role clear and well-defined?",
            "2. Is the tone consistent with the intended purpose?",
            "3. Does the communication style feel natural and appropriate?",
            "4. Are the core values reflected in potential interactions?",
            "5. Does the persona seem knowledgeable in its defined domains?",
            "6. What aspects of the persona could be improved?",
            "7. Is there anything missing from the persona's definition?"
        ]

        feedback = {}
        for q in questions:
            print(f"\n{q}")
            response = input("> ").strip()
            feedback[q] = response

        print("\n--- Evaluation Feedback Captured ---")
        for q, r in feedback.items():
            print(f"{q}\n   Response: {r}\n")
        print("This feedback is valuable for refining your persona.")
        # In a real system, this feedback would be stored and potentially analyzed by an ML model.

    def generate_suggestions(self, persona_to_suggest):
        print(f"\n--- Suggestions for Persona: {persona_to_suggest.name} ---")
        suggestions = []

        # Simple rule-based suggestions
        if not persona_to_suggest.background:
            suggestions.append("Consider adding more detail to the 'Background' to give the bot more character.")
        if not persona_to_suggest.common_phrases:
            suggestions.append("Define some 'Common Phrases' to make the bot's responses more consistent and recognizable.")
        if not persona_to_suggest.goals:
            suggestions.append("Clearly defining 'Goals' helps ensure the bot's actions align with its purpose.")
        if not persona_to_suggest.core_values:
            suggestions.append("Establish 'Core Values' to guide the bot's ethical and moral framework in complex situations.")

        # Check for potential inconsistencies (very basic)
        if "sarcastic" in persona_to_suggest.tone.lower() and "empathy" in [v.lower() for v in persona_to_suggest.core_values]:
            suggestions.append("Warning: A 'sarcastic' tone might conflict with 'empathy' as a core value. Consider how these will balance.")
        if not persona_to_suggest.knowledge_domains and ("support" in persona_to_suggest.role.lower() or "assistant" in persona_to_suggest.role.lower()):
            suggestions.append(f"The bot is a '{persona_to_suggest.role}' but has no defined 'Knowledge Domains'. It needs something to talk about!")

        if suggestions:
            print("Here are some suggestions to enhance your persona:")
            for i, suggestion in enumerate(suggestions):
                print(f"{i+1}. {suggestion}")
        else:
            print("Your persona seems quite complete! No major suggestions at this time.")

    def simulate_interaction(self, persona_to_simulate):
        print(f"\n--- Simulating Interaction with {persona_to_simulate.name} ---")
        print(f"Persona: {persona_to_simulate.name} ({persona_to_simulate.role}, Tone: {persona_to_simulate.tone})")
        print("Type 'exit' to end the simulation.")

        # Generate a sample greeting based on persona
        greeting = f"Hello! As {persona_to_simulate.name}, a {persona_to_simulate.tone} {persona_to_simulate.role}."
        if persona_to_simulate.common_phrases:
            greeting += f" {persona_to_simulate.common_phrases[0]}"
        else:
            greeting += " How may I assist you today?"
        print(f"\nBot: {greeting}")

        while True:
            user_input = input("You: ").strip()
            if user_input.lower() == 'exit':
                print("Simulation ended.")
                break

            # Basic simulation logic reflecting persona attributes
            response = ""
            if any(phrase.lower() in user_input.lower() for phrase in ["hello", "hi", "hey"]):
                response += f"{persona_to_simulate.common_phrases[0] if persona_to_simulate.common_phrases else 'Greetings!'}"
            elif any(domain.lower() in user_input.lower() for domain in persona_to_simulate.knowledge_domains):
                response += f"Ah, you're asking about {user_input.split()[-1]}! As a {persona_to_simulate.role} focused on {', '.join(persona_to_simulate.knowledge_domains[:2])}, I can tell you..."
                if "factual" in persona_to_simulate.tone.lower():
                    response += " [insert factual response placeholder]."
                elif "friendly" in persona_to_simulate.tone.lower():
                    response += " Let me share something exciting about that! [insert friendly detail]."
                elif "sarcastic" in persona_to_simulate.tone.lower():
                    response += " Oh, that old thing? Of course, I'm an expert. [insert sarcastic quip]."
            elif "how are you" in user_input.lower():
                if "friendly" in persona_to_simulate.tone.lower():
                    response += "I'm doing great, thanks for asking! Ready to assist."
                else:
                    response += "I am an AI, I do not have feelings. How can I help you?"
            elif "thank" in user_input.lower():
                 response += f"You're welcome! My goal is to be {persona_to_simulate.goals[0] if persona_to_simulate.goals else 'helpful'}."
                 if persona_to_simulate.common_phrases and len(persona_to_simulate.common_phrases) > 1:
                     response += f" {persona_to_simulate.common_phrases[1]}"
            else:
                response += f"As a {persona_to_simulate.role} with a {persona_to_simulate.tone} communication style, my response is: [reflecting on your input, I can say...]."

            # Add a touch of communication style
            if "verbose" in persona_to_simulate.communication_style.lower():
                response += " Let me elaborate further on that point..."
            elif "concise" in persona_to_simulate.communication_style.lower():
                response = response.split('.')[0] + "."
            if "emoji" in persona_to_simulate.communication_style.lower():
                response += " ✨"

            print(f"Bot: {response}")
            time.sleep(0.5) # Simulate processing time

def main():
    designer = PersonaDesigner()

    while True:
        print("\n--- Adaptive Persona Bot Designer ---")
        print("1. Create New Persona")
        print("2. List All Personas")
        print("3. Edit Persona")
        print("4. Evaluate Persona")
        print("5. Get Persona Suggestions")
        print("6. Simulate Interaction with Persona")
        print("7. Exit")

        choice = input("Enter your choice: ").strip()

        if choice == '1':
            designer.create_persona_guided()
        elif choice == '2':
            designer.list_personas()
        elif choice == '3':
            persona = designer.get_persona_choice()
            if persona:
                designer.edit_persona_guided(persona)
        elif choice == '4':
            persona = designer.get_persona_choice()
            if persona:
                designer.evaluate_persona(persona)
        elif choice == '5':
            persona = designer.get_persona_choice()
            if persona:
                designer.generate_suggestions(persona)
        elif choice == '6':
            persona = designer.get_persona_choice()
            if persona:
                designer.simulate_interaction(persona)
        elif choice == '7':
            print("Exiting Adaptive Persona Bot Designer. Goodbye!")
            break
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()
