from locust import HttpUser, task, between

class FlaskLoadTestUser(HttpUser):
    # Wait time between tasks for a single simulated user
    wait_time = between(1, 3)

    @task(3)
    def index(self):
        self.client.get("/")

    @task(1)
    def health(self):
        self.client.get("/health")

    @task(2)
    def api_data(self):
        self.client.get("/api/data")
