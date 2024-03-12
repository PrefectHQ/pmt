# pmt

`pmt` is a command line tool designed to help you upgrade to new versions of the Prefect Python API.

## Installation

`pmt` can be installed via pip:

```bash
pip install git+https://github.com/PrefectHQ/pmt.git
```

## Usage

Generate new code for a `Deployment.build_from_flow` call:

```bash
pmt migrate build-from-flow path/to/script.py
```

Running the above command on a script containing the following code:

```python
from prefect import flow
from prefect.deployments import Deployment
from prefect.filesystems import GitHub
from prefect.infrastructure import KubernetesJob
from prefect.client.schemas.schedules import IntervalSchedule
from datetime import timedelta


@flow(log_prints=True)
def friendly_flow(name: str = "world"):
    print(f"Hello {name}")


if __name__ == "__main__":
    Deployment.build_from_flow(
        friendly_flow,
        name="my-deployment",
        storage=GitHub.load("my-repo"),
        entrypoint="my_flows.py:friendly_flow",
        infrastructure=KubernetesJob.load("my-job"),
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
```

will produce the following output:

```bash
Refer to the output below to see how to update your code in tests/scripts/infra_and_storage/start.py
────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃                                                 Call 1 of 1: 'my-deployment'                                                 ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

To upgrade to the new deployment API, replace your original code with the updated code below.                                   

                                                         Original Code                                                          

 Deployment.build_from_flow(                                                                                                    
     friendly_flow,                                                                                                             
     name="my-deployment",                                                                                                      
     storage=GitHub.load("my-repo"),                                                                                            
     entrypoint="my_flows.py:friendly_flow",                                                                                    
     infrastructure=KubernetesJob.load("my-job"),                                                                               
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

                                                          Updated Code                                                          

 flow.from_source(                                                                                                              
     source=GitHub.load("my-repo"), entrypoint="my_flows.py:friendly_flow"                                                      
 ).deploy(                                                                                                                      
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

                                                        Additional Info                                                         

 • When deploying flows with flow.deploy, work pools replace infrastructure blocks as the source of infrastructure              
   configuration. To upgrade from an infrastructure block to a work pool, publish your infrastructure as a work pool by calling 
   the .publish_as_work_pool() method on your infrastructure block.and pass the name of the new work pool to the work_pool_name 
   keyword argument of the .deploy() method. To learn more about work pools, see                                                
   https://docs.prefect.io/latest/concepts/work-pools/                                                                          
────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
```

### Write updated code to a file

To write the updated code to a file, use the `--output` flag:

```bash
pmt migrate build-from-flow path/to/script.py --output path/to/output.py
```

To update a file in place, you can provide the same path for the input and output:

```bash
pmt migrate build-from-flow path/to/script.py --output path/to/script.py
```

## Development

- Install [poetry](https://python-poetry.org/docs/#installation)
- Clone this repo
- Run `poetry install` to create a virtual environment, install dependencies, and install `pmt` in editable mode
