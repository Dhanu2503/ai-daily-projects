import json
import os

DATA_FILE = 'skills_data.json'
LEVELS = ["Beginner", "Intermediate", "Advanced", "Expert"]

class Skill:
    """Represents a single skill with its levels and associated learning resources."""
    def __init__(self, name, current_level="Beginner", target_level="Intermediate"):
        if current_level not in LEVELS or target_level not in LEVELS:
            raise ValueError(f"Invalid level provided. Must be one of {LEVELS}")

        self.name = name
        self.current_level = current_level
        self.target_level = target_level
        self.resources = [] # Each resource: {'description': '...', 'completed': False}

    def add_resource(self, description):
        """Adds a new learning resource to the skill."""
        self.resources.append({'description': description, 'completed': False})

    def mark_resource_complete(self, index):
        """Marks a resource as completed based on its index."""
        if 0 <= index < len(self.resources):
            self.resources[index]['completed'] = True
            return True
        return False

    def to_dict(self):
        """Converts the Skill object to a dictionary for JSON serialization."""
        return {
            "name": self.name,
            "current_level": self.current_level,
            "target_level": self.target_level,
            "resources": self.resources
        }

    @classmethod
    def from_dict(cls, data):
        """Creates a Skill object from a dictionary."""
        skill = cls(data['name'], data.get('current_level', 'Beginner'), data.get('target_level', 'Intermediate'))
        skill.resources = data.get('resources', [])
        return skill

    def __str__(self):
        """Returns a user-friendly string representation of the skill."""
        status = f"Skill: {self.name}\n" \
                 f"  Current Level: {self.current_level}\n" \
                 f"  Target Level: {self.target_level}\n" \
                 f"  Resources:"
        if not self.resources:
            status += "\n    No resources added yet."
        else:
            for i, res in enumerate(self.resources):
                status += f"\n    {i+1}. [{'X' if res['completed'] else ' '}] {res['description']}"
        return status

class SkillTracker:
    """Manages a collection of skills, including loading and saving data."""
    def __init__(self, data_file=DATA_FILE):
        self.data_file = data_file
        self.skills = {} # {skill_name: Skill_object}
        self._load_skills()

    def _load_skills(self):
        """Loads skill data from the JSON file."""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    data = json.load(f)
                    for skill_name, skill_data in data.items():
                        self.skills[skill_name] = Skill.from_dict(skill_data)
            except json.JSONDecodeError:
                print(f"Warning: Could not decode JSON from {self.data_file}. Starting with empty skills.")
                self.skills = {}
            except Exception as e:
                print(f"Error loading skills: {e}. Starting with empty skills.")
                self.skills = {}
        else:
            self.skills = {}

    def _save_skills(self):
        """Saves the current skill data to the JSON file."""
        with open(self.data_file, 'w') as f:
            data = {name: skill.to_dict() for name, skill in self.skills.items()}
            json.dump(data, f, indent=4)

    def add_skill(self, name, current_level="Beginner", target_level="Intermediate"):
        """Adds a new skill to the tracker."""
        if name.lower() in [s.lower() for s in self.skills.keys()]: # Case-insensitive check
            print(f"Skill '{name}' already exists (case-insensitive).")
            return False
        try:
            self.skills[name] = Skill(name, current_level, target_level)
            self._save_skills()
            return True
        except ValueError as e:
            print(f"Error adding skill: {e}")
            return False

    def get_skill(self, name):
        """Retrieves a skill by its name."""
        # Case-insensitive lookup
        for skill_name, skill_obj in self.skills.items():
            if skill_name.lower() == name.lower():
                return skill_obj
        return None

    def update_skill_level(self, name, new_current_level=None, new_target_level=None):
        """Updates the current or target level of a skill."""
        skill = self.get_skill(name)
        if skill:
            if new_current_level and new_current_level in LEVELS:
                skill.current_level = new_current_level
            elif new_current_level:
                print(f"Invalid current level '{new_current_level}'. Must be one of {LEVELS}.")
                return False
            
            if new_target_level and new_target_level in LEVELS:
                skill.target_level = new_target_level
            elif new_target_level:
                print(f"Invalid target level '{new_target_level}'. Must be one of {LEVELS}.")
                return False

            self._save_skills()
            return True
        return False

    def add_resource_to_skill(self, skill_name, description):
        """Adds a learning resource to a specific skill."""
        skill = self.get_skill(skill_name)
        if skill:
            skill.add_resource(description)
            self._save_skills()
            return True
        return False

    def mark_resource_complete_for_skill(self, skill_name, resource_index):
        """Marks a resource as complete for a specific skill."""
        skill = self.get_skill(skill_name)
        if skill:
            if skill.mark_resource_complete(resource_index):
                self._save_skills()
                return True
        return False

    def list_skills(self):
        """Returns a list of all managed Skill objects."""
        return list(self.skills.values())

# CLI Utility Functions
def display_menu():
    """Prints the main menu options."""
    print("\n--- SkillUp Tracker Menu ---")
    print("1. Add New Skill")
    print("2. View All Skills")
    print("3. Update Skill Level")
    print("4. Add Learning Resource to Skill")
    print("5. Mark Resource as Complete")
    print("6. Exit")
    print("----------------------------")

def get_input(prompt, validation_func=None, error_msg="Invalid input. Please try again."):
    """Gets validated string input from the user."""
    while True:
        value = input(prompt).strip()
        if not value:
            print("Input cannot be empty.")
            continue
        if validation_func is None or validation_func(value):
            return value
        print(error_msg)

def get_int_input(prompt, min_val=None, max_val=None):
    """Gets validated integer input from the user."""
    while True:
        try:
            value = int(input(prompt).strip())
            if (min_val is None or value >= min_val) and \
               (max_val is None or value <= max_val):
                return value
            else:
                print(f"Please enter a number between {min_val or '-inf'} and {max_val or 'inf'}.")
        except ValueError:
            print("Invalid input. Please enter a number.")

def main():
    """Main function to run the SkillUp Tracker CLI application."""
    tracker = SkillTracker()

    while True:
        display_menu()
        choice = get_input("Enter your choice: ", lambda x: x.isdigit() and 1 <= int(x) <= 6, "Invalid choice. Please enter a number from 1 to 6.")

        if choice == '1': # Add New Skill
            name = get_input("Enter skill name: ")
            current_level = get_input(f"Enter current level ({'/'.join(LEVELS)}): ", lambda x: x.capitalize() in LEVELS, f"Level must be one of: {', '.join(LEVELS)}").capitalize()
            target_level = get_input(f"Enter target level ({'/'.join(LEVELS)}): ", lambda x: x.capitalize() in LEVELS, f"Level must be one of: {', '.join(LEVELS)}").capitalize()
            if tracker.add_skill(name, current_level, target_level):
                print(f"Skill '{name}' added successfully.")

        elif choice == '2': # View All Skills
            skills = tracker.list_skills()
            if not skills:
                print("No skills added yet.")
            else:
                print("\n--- Your Skills ---")
                for skill in skills:
                    print(skill)
                    print("-------------------")

        elif choice == '3': # Update Skill Level
            skill_name = get_input("Enter the name of the skill to update: ")
            skill = tracker.get_skill(skill_name)
            if not skill:
                print(f"Skill '{skill_name}' not found.")
                continue

            print(f"\nCurrent levels for {skill.name}: Current={skill.current_level}, Target={skill.target_level}")
            
            new_current_level = None
            if get_input("Update current level? (y/n): ").lower() == 'y':
                new_current_level = get_input(f"Enter new current level ({'/'.join(LEVELS)}): ", lambda x: x.capitalize() in LEVELS, f"Level must be one of: {', '.join(LEVELS)}").capitalize()

            new_target_level = None
            if get_input("Update target level? (y/n): ").lower() == 'y':
                new_target_level = get_input(f"Enter new target level ({'/'.join(LEVELS)}): ", lambda x: x.capitalize() in LEVELS, f"Level must be one of: {', '.join(LEVELS)}").capitalize()

            if new_current_level or new_target_level:
                if tracker.update_skill_level(skill_name, new_current_level, new_target_level):
                    print(f"Skill '{skill_name}' levels updated.")
                else:
                    print("Failed to update skill levels.")
            else:
                print("No level updates requested.")


        elif choice == '4': # Add Learning Resource to Skill
            skill_name = get_input("Enter the name of the skill to add a resource to: ")
            skill = tracker.get_skill(skill_name)
            if not skill:
                print(f"Skill '{skill_name}' not found.")
                continue
            
            description = get_input("Enter resource description: ")
            if tracker.add_resource_to_skill(skill_name, description):
                print(f"Resource added to '{skill_name}'.")
            else:
                print("Failed to add resource.")

        elif choice == '5': # Mark Resource as Complete
            skill_name = get_input("Enter the name of the skill to mark a resource complete for: ")
            skill = tracker.get_skill(skill_name)
            if not skill:
                print(f"Skill '{skill_name}' not found.")
                continue
            
            print(f"\n--- Resources for {skill.name} ---")
            if not skill.resources:
                print("No resources for this skill.")
                continue

            for i, res in enumerate(skill.resources):
                status = "COMPLETED" if res['completed'] else "PENDING"
                print(f"{i+1}. [{status}] {res['description']}")

            resource_index = get_int_input("Enter the number of the resource to mark complete: ", min_val=1, max_val=len(skill.resources))
            
            if tracker.mark_resource_complete_for_skill(skill_name, resource_index - 1): # -1 for 0-based index
                print(f"Resource '{skill.resources[resource_index-1]['description']}' marked as complete.")
            else:
                print("Failed to mark resource complete.")

        elif choice == '6': # Exit
            print("Exiting SkillUp Tracker. Goodbye!")
            break

if __name__ == "__main__":
    main()
