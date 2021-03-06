# This is just example of test for pytest
import logging
import pytest

from ocs_ci.ocs import ocp

from ocs_ci.framework import config
from ocs_ci.framework.testlib import run_this, EcosystemTest, tier1


logger = logging.getLogger(__name__)

OCP = ocp.OCP(
    kind='pods', namespace=config.ENV_DATA['cluster_namespace']
)

EXAMPLE_MSG = "THIS IS JUST AN EXAMPLE OF PYTEST TEST, WE WON'T RUN IT!"


@pytest.mark.skip(EXAMPLE_MSG)
@run_this
def test_not_run_me_fail_pass():
    logger.info("Hey from test which should pass")
    logger.info(
        "You can easily access data from config.ENV_DATA like cluster_name: %s",
        config.ENV_DATA['cluster_name']
    )
    assert 1 == 1, "This will not reach this message"


@pytest.mark.skip(EXAMPLE_MSG)
@tier1
class TestExampleClass(EcosystemTest):
    def test_example_method(self):
        logger.info("Hello from test method inside test class")
        pods = OCP.get()['items']
        number_of_pods = len(pods)
        logger.info(
            f"Found {number_of_pods} pods in namespace: "
            f"{config.ENV_DATA['cluster_namespace']}"
        )
        for pod in pods:
            logger.info(f"Pod : {pod.metadata.name}")
        assert number_of_pods, "No pod exists!"
