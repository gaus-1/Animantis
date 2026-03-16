from locust import HttpUser, between, task


class AnimantisDBStressTest(HttpUser):
    wait_time = between(0.1, 0.5)

    @task(5)
    def get_world_zones(self):
        # This endpoint makes multiple DB queries
        self.client.get("/api/v1/world/zones")

    @task(1)
    def check_health(self):
        self.client.get("/health")
