import asyncio
from exercise_api import get_exercises_by_target
from food_api import async_search_foods

def generare_workout_plan(goal):
    """
    Generate a workout plan based on the user's fitness goal.
    """
    if goal == "muscle_gain":
        target = "biceps"  # Example target for muscle gain
    elif goal == "weight_loss":
        target = "cardio"  # Example target for weight loss
    else:
        target = "full_body"

    exercises = get_exercises_by_target(target)
    if not exercises:
        return {"error": "No exercises found for the specified target"}

    workout_plan = exercises[:5]  # Limit to first 5 exercises

    return workout_plan

async def generate_meal_plan(dietary_preference):
    """
    Generate a meal plan based on the user's dietary preference.
    """

    foods = await async_search_foods(dietary_preference)
    if not foods:
        return {"error": "No food products found for the specified dietary preference"}

    meal_plan = foods[:5]  # Limit to first 5 food items

    return meal_plan