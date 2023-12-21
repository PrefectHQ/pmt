from prefect import flow
from prefect.deployments import Deployment
from prefect.client.schemas.schedules import IntervalSchedule
from datetime import timedelta


@flow(log_prints=True)
def friendly_flow(name: str = "world"):
    print(f"Hello {name}")


if __name__ == "__main__":
    Deployment.build_from_flow(
        friendly_flow,
        name="my-deployment",
        storage="github/my-repo",
        entrypoint="my_flows.py:friendly_flow",
        infrastructure="kubernetes-job/my-job",
        schedule=IntervalSchedule(timedelta(hours=1)),
        tags=["my-tag"],
        version="test",
        description="my-description",
        work_pool_name="default-agent-pool",
        work_queue_name="my-work-queue",
        infra_overrides={"env": {"MY_ENV_VAR": "my-env-var-value"}},
        is_schedule_active=True,
        parameters={"name": "Marvin"},
    )
