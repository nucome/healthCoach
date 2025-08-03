from locust import HttpUser, task, between

class HealthCoachUser(HttpUser):
    wait_time = between(1, 2)  # Wait time between tasks


    @task()
    def send_request(self):
        self.client.post("/", json={
            "goal": "muscle_gain",
            "dietary_preference": "vegan"
        })  # Simulate a GET request to the /about URL