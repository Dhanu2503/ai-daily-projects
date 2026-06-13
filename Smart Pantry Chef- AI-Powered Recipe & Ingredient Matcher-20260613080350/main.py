import collections
from datetime import datetime, timedelta
import re

# Data structures
class Ingredient:
    def __init__(self, name: str, quantity: float, unit: str = "unit", expiry_date: datetime = None):
        self.name = name.lower()
        self.quantity = quantity
        self.unit = unit
        self.expiry_date = expiry_date

    def __repr__(self):
        expiry_str = f", Expires: {self.expiry_date.strftime('%Y-%m-%d')}" if self.expiry_date else ""
        return f"Ingredient(name='{self.name}', quantity={self.quantity} {self.unit}{expiry_str})"

    def to_dict(self):
        return {
            "name": self.name,
            "quantity": self.quantity,
            "unit": self.unit,
            "expiry_date": self.expiry_date.strftime('%Y-%m-%d') if self.expiry_date else None
        }

    @staticmethod
    def from_dict(data):
        expiry = datetime.strptime(data["expiry_date"], '%Y-%m-%d') if data["expiry_date"] else None
        return Ingredient(data["name"], data["quantity"], data["unit"], expiry)


class RecipeIngredient:
    def __init__(self, name: str, quantity: float, unit: str = "unit"):
        self.name = name.lower()
        self.quantity = quantity
        self.unit = unit

    def __repr__(self):
        return f"RecipeIngredient(name='{self.name}', quantity={self.quantity} {self.unit})"

    def to_dict(self):
        return {
            "name": self.name,
            "quantity": self.quantity,
            "unit": self.unit
        }

    @staticmethod
    def from_dict(data):
        return RecipeIngredient(data["name"], data["quantity"], data["unit"])


class Recipe:
    def __init__(self, name: str, ingredients: list[RecipeIngredient], instructions: list[str], category: str = "General"):
        self.name = name
        self.ingredients = ingredients
        self.instructions = instructions
        self.category = category

    def __repr__(self):
        return f"Recipe(name='{self.name}', category='{self.category}')"

    def to_dict(self):
        return {
            "name": self.name,
            "ingredients": [i.to_dict() for i in self.ingredients],
            "instructions": self.instructions,
            "category": self.category
        }

    @staticmethod
    def from_dict(data):
        ingredients = [RecipeIngredient.from_dict(i) for i in data["ingredients"]]
        return Recipe(data["name"], ingredients, data["instructions"], data["category"])


class Pantry:
    def __init__(self):
        # Store ingredients as {name: [Ingredient objects]} to handle multiple items of same type with different expiries
        self.ingredients: collections.defaultdict[str, list[Ingredient]] = collections.defaultdict(list)

    def add_ingredient(self, name: str, quantity: float, unit: str = "unit", expiry_days: int = None):
        expiry_date = None
        if expiry_days is not None:
            expiry_date = datetime.now() + timedelta(days=expiry_days)
        
        new_ingredient = Ingredient(name, quantity, unit, expiry_date)
        self.ingredients[name.lower()].append(new_ingredient)
        self.ingredients[name.lower()].sort(key=lambda x: x.expiry_date if x.expiry_date else datetime.max) # Keep oldest expiry first

        print(f"Added {quantity} {unit} of {name} to pantry.")

    def remove_ingredient(self, name: str, quantity_to_remove: float):
        name_lower = name.lower()
        if name_lower not in self.ingredients or not self.ingredients[name_lower]:
            print(f"Error: {name.capitalize()} not found in pantry.")
            return False

        removed_count = 0
        original_total_quantity = sum(i.quantity for i in self.ingredients[name_lower])

        if quantity_to_remove <= 0:
            print("Quantity to remove must be positive.")
            return False
        if quantity_to_remove > original_total_quantity:
            print(f"Not enough {name.capitalize()} in pantry. You have {original_total_quantity:.1f}, but tried to remove {quantity_to_remove:.1f}.")
            return False

        temp_ingredients = []

        # Consume from oldest expiry first
        self.ingredients[name_lower].sort(key=lambda x: x.expiry_date if x.expiry_date else datetime.max)

        while quantity_to_remove > 0 and self.ingredients[name_lower]:
            current_item = self.ingredients[name_lower].pop(0) # Take the oldest expiring item
            
            if current_item.quantity <= quantity_to_remove:
                quantity_to_remove -= current_item.quantity
                removed_count += current_item.quantity
            else:
                removed_count += quantity_to_remove
                current_item.quantity -= quantity_to_remove
                quantity_to_remove = 0
                temp_ingredients.append(current_item) # Put back remaining
        
        # Put back any remaining items
        if temp_ingredients:
            self.ingredients[name_lower].extend(temp_ingredients)
            self.ingredients[name_lower].sort(key=lambda x: x.expiry_date if x.expiry_date else datetime.max)

        if removed_count > 0:
            print(f"Removed {removed_count:.1f} of {name.capitalize()} from pantry.")
            if not self.ingredients[name_lower]:
                del self.ingredients[name_lower]
            return True
        return False # Should not be reached if initial checks are good

    def get_total_quantity(self, name: str) -> float:
        name_lower = name.lower()
        return sum(item.quantity for item in self.ingredients[name_lower]) if name_lower in self.ingredients else 0.0
    
    def get_available_ingredients(self):
        # Returns a simplified dict of current available quantities for easier lookup
        available = collections.defaultdict(float)
        for name, items in self.ingredients.items():
            for item in items:
                # Only count non-expired items
                if not item.expiry_date or item.expiry_date >= datetime.now():
                    available[item.name] += item.quantity
        return dict(available)

    def view_pantry(self):
        if not self.ingredients:
            print("Your pantry is empty.")
            return

        print("\n--- Your Pantry ---")
        all_items = []
        for name, items in self.ingredients.items():
            for item in items:
                all_items.append(item)
        
        # Sort by expiry date (oldest first), then by name
        all_items.sort(key=lambda x: (x.expiry_date if x.expiry_date else datetime.max, x.name))

        for item in all_items:
            expiry_info = f" (Expires: {item.expiry_date.strftime('%Y-%m-%d')})" if item.expiry_date else ""
            if item.expiry_date and item.expiry_date < datetime.now():
                expiry_info += " (EXPIRED!)"
            elif item.expiry_date and item.expiry_date < datetime.now() + timedelta(days=7):
                expiry_info += " (Expiring Soon!)"
            print(f"- {item.name.capitalize()}: {item.quantity:.1f} {item.unit}{expiry_info}")
        print("-------------------\n")


class RecipeDatabase:
    def __init__(self):
        self.recipes: list[Recipe] = []
        self._load_sample_recipes()

    def add_recipe(self, recipe: Recipe):
        self.recipes.append(recipe)

    def get_recipe_by_name(self, name: str) -> Recipe | None:
        # Simple fuzzy matching for recipe names
        name_lower = name.lower()
        best_match = None
        highest_score = 0

        for recipe in self.recipes:
            recipe_name_lower = recipe.name.lower()
            if name_lower == recipe_name_lower:
                return recipe # Exact match
            
            # Simple substring or word match scoring
            score = 0
            if name_lower in recipe_name_lower:
                score += 5 # Substring match
            if any(word in recipe_name_lower for word in name_lower.split()):
                score += 3 # Word match
            
            if score > highest_score:
                highest_score = score
                best_match = recipe

        if highest_score > 0 and highest_score >= 3: # Require a minimum score for suggestion
            print(f"Did not find exact match for '{name}'. Showing details for closest match: '{best_match.name}'.")
            return best_match
            
        return None

    def _load_sample_recipes(self):
        # Sample Recipe 1: Classic Omelette
        self.add_recipe(Recipe(
            name="Classic Omelette",
            ingredients=[
                RecipeIngredient("eggs", 2, "large"),
                RecipeIngredient("milk", 2, "tbsp"),
                RecipeIngredient("butter", 1, "tsp"),
                RecipeIngredient("salt", 0.25, "tsp"),
                RecipeIngredient("black pepper", 0.1, "tsp")
            ],
            instructions=[
                "Crack eggs into a bowl, add milk, salt, and pepper. Whisk until well combined.",
                "Melt butter in a non-stick pan over medium heat.",
                "Pour egg mixture into the pan. Cook for 2-3 minutes, gently pushing cooked egg from the edges to the center.",
                "When eggs are mostly set but still a little runny on top, fold the omelette in half and slide onto a plate."
            ],
            category="Breakfast"
        ))

        # Sample Recipe 2: Pasta Aglio e Olio
        self.add_recipe(Recipe(
            name="Pasta Aglio e Olio",
            ingredients=[
                RecipeIngredient("spaghetti", 200, "g"),
                RecipeIngredient("garlic", 4, "cloves"),
                RecipeIngredient("olive oil", 60, "ml"),
                RecipeIngredient("red pepper flakes", 0.5, "tsp"),
                RecipeIngredient("parsley", 10, "g"),
                RecipeIngredient("salt", 1, "tsp")
            ],
            instructions=[
                "Cook spaghetti according to package directions until al dente. Reserve 1 cup pasta water, then drain.",
                "While pasta cooks, thinly slice garlic.",
                "In a large skillet, heat olive oil over medium-low heat. Add garlic and red pepper flakes. Sauté gently until garlic is fragrant and lightly golden, about 3-5 minutes. Do not burn the garlic!",
                "Add cooked spaghetti to the skillet. Toss to coat.",
                "Add about 1/2 cup reserved pasta water and chopped parsley. Toss vigorously to create a light sauce. Add more pasta water if needed for desired consistency.",
                "Season with salt to taste and serve immediately."
            ],
            category="Dinner"
        ))

        # Sample Recipe 3: Simple Tomato Salad
        self.add_recipe(Recipe(
            name="Simple Tomato Salad",
            ingredients=[
                RecipeIngredient("tomatoes", 2, "medium"),
                RecipeIngredient("red onion", 0.25, "medium"),
                RecipeIngredient("basil", 5, "leaves"),
                RecipeIngredient("olive oil", 1, "tbsp"),
                RecipeIngredient("balsamic vinegar", 1, "tsp"),
                RecipeIngredient("salt", 0.25, "tsp"),
                RecipeIngredient("black pepper", 0.1, "tsp")
            ],
            instructions=[
                "Slice tomatoes into wedges. Thinly slice red onion.",
                "Roughly chop basil leaves.",
                "In a bowl, combine tomatoes, red onion, and basil.",
                "Drizzle with olive oil and balsamic vinegar. Season with salt and pepper.",
                "Toss gently and serve."
            ],
            category="Side Dish"
        ))
        
        # Sample Recipe 4: Chicken Stir-fry
        self.add_recipe(Recipe(
            name="Chicken Stir-fry",
            ingredients=[
                RecipeIngredient("chicken breast", 300, "g"),
                RecipeIngredient("broccoli", 1, "head"),
                RecipeIngredient("carrot", 1, "medium"),
                RecipeIngredient("soy sauce", 3, "tbsp"),
                RecipeIngredient("ginger", 1, "tbsp"),
                RecipeIngredient("garlic", 2, "cloves"),
                RecipeIngredient("sesame oil", 1, "tsp"),
                RecipeIngredient("rice", 200, "g") # Assuming rice is cooked separately and the quantity here is for serving
            ],
            instructions=[
                "Cut chicken into bite-sized pieces. Chop broccoli into florets, slice carrot.",
                "Mince ginger and garlic.",
                "Heat sesame oil in a wok or large skillet over high heat.",
                "Add chicken and stir-fry until cooked through. Remove from pan.",
                "Add broccoli and carrots to the pan, stir-fry for 3-5 minutes until tender-crisp.",
                "Add ginger and garlic, stir-fry for 30 seconds until fragrant.",
                "Return chicken to the pan. Pour in soy sauce and toss everything to combine.",
                "Serve immediately with cooked rice."
            ],
            category="Dinner"
        ))


class SmartPantryChef:
    def __init__(self):
        self.pantry = Pantry()
        self.recipe_db = RecipeDatabase()

    def _calculate_recipe_match_score(self, recipe: Recipe, available_ingredients: dict) -> dict:
        missing_ingredients_list = [] # List of (name, quantity, unit) needed
        fully_available_count = 0
        partially_available_count = 0
        total_recipe_ingredients_count = len(recipe.ingredients)
        
        for req_ing in recipe.ingredients:
            pantry_qty = available_ingredients.get(req_ing.name, 0.0)
            
            if pantry_qty >= req_ing.quantity:
                fully_available_count += 1
            elif pantry_qty > 0:
                partially_available_count += 1
                missing_ingredients_list.append({"name": req_ing.name, "needed": req_ing.quantity - pantry_qty, "unit": req_ing.unit})
            else:
                missing_ingredients_list.append({"name": req_ing.name, "needed": req_ing.quantity, "unit": req_ing.unit})
        
        # Scoring logic for 'AI-powered' recommendation:
        # 1. Prioritize recipes with more fully available ingredients.
        # 2. Then, prioritize recipes with fewer total missing ingredients.
        # 3. Give a slight bonus for recipes with ingredients partially available (less to buy).
        
        match_percentage = (fully_available_count / total_recipe_ingredients_count) * 100 if total_recipe_ingredients_count > 0 else 0
        
        # Score calculation:
        # - Large positive for fully available ingredients
        # - Small positive for partially available ingredients
        # - Large negative for completely missing ingredients
        score = (fully_available_count * 100) + (partially_available_count * 20) - (len(missing_ingredients_list) * 50)

        return {
            "recipe": recipe,
            "match_percentage": match_percentage,
            "missing_ingredients_count": len(missing_ingredients_list),
            "ingredients_to_buy": missing_ingredients_list,
            "score": score
        }

    def find_recipes(self):
        available_ingredients = self.pantry.get_available_ingredients()
        
        recipe_scores_data = []
        for recipe in self.recipe_db.recipes:
            score_data = self._calculate_recipe_match_score(recipe, available_ingredients)
            recipe_scores_data.append(score_data)
        
        # Sort by score in descending order
        recipe_scores_data.sort(key=lambda x: x["score"], reverse=True)

        print("\n--- Recommended Recipes ---")
        if not recipe_scores_data:
            print("No recipes found in the database.")
            return

        displayed_count = 0
        for i, data in enumerate(recipe_scores_data):
            recipe = data["recipe"]
            match_percent = data["match_percentage"]
            missing_count = data["missing_ingredients_count"]
            ingredients_to_buy = data["ingredients_to_buy"]

            # Filter out very low-scoring recipes if too many exist
            if displayed_count >= 5 and data["score"] < -100: # Heuristic threshold
                print("... (More recipes available with many missing ingredients)")
                break

            print(f"\n{i+1}. {recipe.name} ({recipe.category})")
            print(f"   Match: {match_percent:.0f}% of ingredients available.")
            
            if missing_count == 0:
                print("   You have all ingredients! 🎉")
            else:
                print(f"   Missing {missing_count} ingredients:")
                for ing in ingredients_to_buy:
                    print(f"     - {ing['name'].capitalize()}: {ing['needed']:.1f} {ing['unit']} needed")
            
            displayed_count += 1
        print("---------------------------\n")

    def view_recipe_details(self, recipe_name: str):
        recipe = self.recipe_db.get_recipe_by_name(recipe_name)
        if not recipe:
            print(f"Recipe '{recipe_name}' not found.")
            return
        
        print(f"\n--- Recipe: {recipe.name} ({recipe.category}) ---")
        print("\nIngredients:")
        available_ingredients_in_pantry = self.pantry.get_available_ingredients()

        for ing in recipe.ingredients:
            pantry_qty = available_ingredients_in_pantry.get(ing.name, 0.0)
            status = ""
            if pantry_qty >= ing.quantity:
                status = " (✅ Available)"
            elif pantry_qty > 0:
                status = f" (⚠️ Partially available: {pantry_qty:.1f} {ing.unit}, need {ing.quantity - pantry_qty:.1f} more)"
            else:
                status = " (❌ Missing)"
            print(f"- {ing.name.capitalize()}: {ing.quantity:.1f} {ing.unit}{status}")
        
        print("\nInstructions:")
        for i, step in enumerate(recipe.instructions):
            print(f"{i+1}. {step}")
        print("---------------------------------------\n")


def run_cli():
    chef = SmartPantryChef()

    print("Welcome to Smart Pantry Chef: AI-Powered Recipe & Ingredient Matcher!")

    while True:
        print("\n--- Main Menu ---")
        print("1. Add Ingredient to Pantry")
        print("2. Remove Ingredient from Pantry")
        print("3. View Pantry")
        print("4. Find Recipes")
        print("5. View Recipe Details")
        print("6. Exit")
        choice = input("Enter your choice: ").strip()

        if choice == '1':
            name = input("Enter ingredient name: ").strip()
            if not name:
                print("Ingredient name cannot be empty.")
                continue
            try:
                quantity = float(input("Enter quantity (e.g., 200 for grams, 2 for pieces): "))
                if quantity <= 0:
                    print("Quantity must be a positive number.")
                    continue
                unit = input("Enter unit (e.g., g, ml, pcs, tbsp, cup): ").strip()
                if not unit:
                    unit = "unit"
                expiry_input = input("Enter expiry in days from now (optional, press Enter to skip): ").strip()
                expiry_days = int(expiry_input) if expiry_input else None
                if expiry_days is not None and expiry_days < 0:
                    print("Expiry days cannot be negative.")
                    continue
                chef.pantry.add_ingredient(name, quantity, unit, expiry_days)
            except ValueError:
                print("Invalid quantity or expiry days. Please enter a valid number.")
        
        elif choice == '2':
            name = input("Enter ingredient name to remove: ").strip()
            if not name:
                print("Ingredient name cannot be empty.")
                continue
            try:
                quantity = float(input("Enter quantity to remove: "))
                chef.pantry.remove_ingredient(name, quantity)
            except ValueError:
                print("Invalid quantity. Please enter a valid number.")
        
        elif choice == '3':
            chef.pantry.view_pantry()
        
        elif choice == '4':
            chef.find_recipes()
        
        elif choice == '5':
            recipe_name = input("Enter the name of the recipe you want to view: ").strip()
            if not recipe_name:
                print("Recipe name cannot be empty.")
                continue
            chef.view_recipe_details(recipe_name)

        elif choice == '6':
            print("Thank you for using Smart Pantry Chef! Goodbye!")
            break
        
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    run_cli()
