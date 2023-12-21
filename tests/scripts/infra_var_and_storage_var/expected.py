from prefect import flow
from prefect.deployments import Deployment
from prefect.filesystems import GitHub
from prefect.infrastructure import KubernetesJob
from prefect.client.schemas.schedules import IntervalSchedule
from datetime import timedelta


@flow(log_prints=True)
def friendly_flow(name: str = "world"):
    print(f"Hello {name}")


infra = KubernetesJob.load("my-job-default-image")
storage = GitHub.load("my-repo")
if __name__ == "__main__":
    flow.from_source(source=storage, entrypoint="my_flows.py:friendly_flow").deploy(
        name="my-deployment",
        description="my-description",
        version="test",
        tags=["my-tag"],
        schedule=IntervalSchedule(timedelta(hours=1)),
        parameters={"name": "Marvin"},
        is_schedule_active=True,
        work_pool_name="default-agent-pool",
        work_queue_name="my-work-queue",
        job_variables={"env": {"MY_ENV_VAR": "my-env-var-value"}},
    )
