import os
from urllib.request import Request

import gradio as gr
from recommendations import generare_workout_plan, generate_meal_plan
from loguru import logger
from prometheus_client import start_http_server, Summary
import asyncio

logger.add("app.log", rotation="1 MB", retention="10 days", level="INFO")

REQUEST_TIME = Summary('request_processing_seconds', 'Time spent processing request')

@REQUEST_TIME.time()
def health_coach(goal, dietary_preference):
    """
    Main function to handle the health coaching app logic.
    """
    logger.info(f"Received request with goal: {goal}, dietary preference: {dietary_preference}")
    try:
        # Generate workout plan
        workout_plan = generare_workout_plan(goal)
        logger.info(f"Generated workout plan: {workout_plan}")

        # Generate meal plan
        meal_plan = asyncio.run(generate_meal_plan(dietary_preference))
        logger.info(f"Generated meal plan: {meal_plan}")

        return workout_plan, meal_plan
    except Exception as e:
        logger.error(f"Error processing request: {e}")
        return {"error": str(e)}, {"error": str(e)}

app = gr.Interface(
    fn=health_coach,
    inputs=[
        gr.Textbox(label="Fitness Goal", placeholder="e.g., muscle_gain, weight_loss"),
        gr.Textbox(label="Dietary Preference", placeholder="e.g., vegan, vegetarian")
    ],
    outputs=[
        gr.JSON(label="Workout Plan"),
        gr.JSON(label="Meal Plan")
    ],
    title="Health Coach App",
    description="Generate personalized workout and meal plans based on your fitness goals and dietary preferences."
)

if __name__ == "__main__":
    port = int(os.getenv("PORT", 7860))  # Default Gradio port

    logger.info("Starting Gradio app...")
    app.launch(server_name="0.0.0.0", server_port=port)