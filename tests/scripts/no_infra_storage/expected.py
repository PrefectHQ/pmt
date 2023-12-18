from prefect import flow
from prefect.client.schemas.schedules import CronSchedule
from prefect.filesystems import GitHub


@flow(log_prints=True)
def friendly_flow(name: str = "world"):
    print(f"Hello {name}")


if __name__ == "__main__":
    flow.from_source(
        source=GitHub.load("my-repo"), entrypoint="my_flows.py:friendly_flow"
    ).serve(
        name="my-deployment",
        description="my-description",
        version="test",
        tags=["my-tag"],
        schedule=CronSchedule("0 0 * * *"),
        parameters={"name": "Marvin"},
        is_schedule_active=True,
        work_pool_name="default-agent-pool",
        work_queue_name="my-work-queue",
    )
