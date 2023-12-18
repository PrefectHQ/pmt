from prefect import flow
from prefect.deployments import Deployment
from prefect.client.schemas.schedules import CronSchedule


@flow(log_prints=True)
def friendly_flow(name: str = "world"):
    print(f"Hello {name}")


if __name__ == "__main__":
    Deployment.build_from_flow(
        friendly_flow,
        name="my-deployment",
        schedule=CronSchedule("0 0 * * *"),
        tags=["my-tag"],
        version="test",
        description="my-description",
        work_pool_name="default-agent-pool",
        work_queue_name="my-work-queue",
        is_schedule_active=True,
        parameters={"name": "Marvin"},
    )
