import collections

CULINARY_DATA = {
    "Spaghetti Bolognese": [
        "spaghetti", "ground beef", "tomato sauce", "onion", "garlic", "carrots",
        "celery", "oregano", "basil", "parmesan cheese", "olive oil", "salt", "pepper"
    ],
    "Chicken Curry": [
        "chicken breast", "curry powder", "coconut milk", "onion", "garlic", "ginger",
        "tomatoes", "rice", "coriander", "turmeric", "cumin", "chili powder", "salt"
    ],
    "Vegetable Soup": [
        "carrots", "potatoes", "celery", "onion", "garlic", "vegetable broth",
        "tomatoes", "peas", "green beans", "parsley", "salt", "pepper", "olive oil"
    ],
    "Tacos": [
        "tortillas", "ground beef", "lettuce", "tomato", "onion", "cheese",
        "salsa", "sour cream", "chili powder", "cumin", "garlic powder", "salt"
    ],
    "Pancakes": [
        "flour", "eggs", "milk", "baking powder", "sugar", "butter",
        "maple syrup", "berries"
    ],
    "Caesar Salad": [
        "romaine lettuce", "croutons", "parmesan cheese", "caesar dressing",
        "chicken breast" # Optional, but common
    ],
    "Mushroom Risotto": [
        "arborio rice", "mushrooms", "onion", "garlic", "chicken broth",
        "white wine", "parmesan cheese", "butter", "olive oil", "parsley", "salt", "pepper"
    ],
    "Beef Stir-fry": [
        "beef sirloin", "broccoli", "carrots", "bell peppers", "soy sauce",
        "ginger", "garlic", "sesame oil", "rice", "onion"
    ]
}

def preprocess_ingredient(ingredient):
    """Standardize ingredient names."""
    return ingredient.strip().lower()

def predict_ingredients(current_ingredients, top_n_recipes=3, min_matches=1):
    """
    Predicts additional ingredients based on current ingredients.

    Args:
        current_ingredients (list): A list of ingredients already chosen.
        top_n_recipes (int): Number of top matching recipes to consider for suggestions.
        min_matches (int): Minimum number of shared ingredients for a recipe to be considered.

    Returns:
        set: A set of unique suggested ingredients.
    """
    if not current_ingredients:
        return set()

    processed_current = {preprocess_ingredient(ing) for ing in current_ingredients}

    recipe_scores = []
    for recipe_name, recipe_ingredients in CULINARY_DATA.items():
        processed_recipe_ingredients = {preprocess_ingredient(ing) for ing in recipe_ingredients}
        
        # Calculate overlap
        common_ingredients = processed_current.intersection(processed_recipe_ingredients)
        score = len(common_ingredients)
        
        if score >= min_matches:
            recipe_scores.append((score, recipe_name, processed_recipe_ingredients))

    # Sort by score in descending order
    recipe_scores.sort(key=lambda x: x[0], reverse=True)

    suggested_ingredients = set()
    considered_recipes_count = 0

    for score, recipe_name, recipe_ingredients_set in recipe_scores:
        if considered_recipes_count >= top_n_recipes:
            break
        
        # Only consider recipes that contribute new suggestions
        potential_suggestions = recipe_ingredients_set - processed_current
        if potential_suggestions:
            suggested_ingredients.update(potential_suggestions)
            considered_recipes_count += 1 # Only increment if this recipe contributes

    # Filter out ingredients already in current_ingredients (should already be handled by set subtraction)
    # And filter out very generic ones that might not be helpful (e.g., salt, pepper, water, oil, if not specific)
    # This is a heuristic and can be improved.
    GENERIC_EXCLUSIONS = {"salt", "pepper", "water", "oil", "olive oil", "butter"}
    final_suggestions = suggested_ingredients - processed_current - GENERIC_EXCLUSIONS

    return final_suggestions

def main():
    print("Welcome to the Culinary Ingredient Predictor!")
    print("Enter the ingredients you already have, separated by commas (e.g., chicken, onion, garlic)")
    
    user_input = input("Your ingredients: ")
    
    if not user_input.strip():
        print("No ingredients entered. Cannot provide suggestions.")
        return

    input_ingredients_list = [ing.strip() for ing in user_input.split(',') if ing.strip()]
    
    if not input_ingredients_list:
        print("No valid ingredients found after parsing. Cannot provide suggestions.")
        return

    suggestions = predict_ingredients(input_ingredients_list)

    if suggestions:
        print("\nBased on your ingredients, you might also consider adding:")
        for i, ing in enumerate(sorted(list(suggestions))):
            print(f"- {ing.title()}")
    else:
        print("\nCould not find significant suggestions based on your ingredients. Try adding more common ingredients.")

if __name__ == "__main__":
    main()
