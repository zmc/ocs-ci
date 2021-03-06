import logging
import pytest
from ocs_ci.framework.testlib import tier1, ManageTest
from tests import helpers
from ocs_ci.ocs import ocp, constants
from ocs_ci.ocs.resources.pod import list_ceph_images
from ocs_ci.ocs.exceptions import CommandFailed

log = logging.getLogger(__name__)


@pytest.fixture(scope='class')
def test_fixture(request):
    """
    This is a test fixture
    """
    self = request.node.cls

    def finalizer():
        teardown(self)

    request.addfinalizer(finalizer)
    setup(self)


def setup(self):
    """
    Setting up a secret and storage class
    """

    self.secret_obj = helpers.create_secret(constants.CEPHBLOCKPOOL)
    self.sc_obj_retain = helpers.create_storage_class(
        interface_type=constants.CEPHBLOCKPOOL,
        interface_name=constants.DEFAULT_BLOCKPOOL,
        secret_name=self.secret_obj.name,
        reclaim_policy=constants.RECLAIM_POLICY_RETAIN
    )
    self.sc_obj_delete = helpers.create_storage_class(
        interface_type=constants.CEPHBLOCKPOOL,
        interface_name=constants.DEFAULT_BLOCKPOOL,
        secret_name=self.secret_obj.name,
        reclaim_policy=constants.RECLAIM_POLICY_DELETE
    )


def teardown(self):
    """
    Deleting secret
    """
    assert self.sc_obj_retain.delete()
    assert self.sc_obj_delete.delete()
    assert self.secret_obj.delete()


@tier1
@pytest.mark.usefixtures(test_fixture.__name__)
class TestReclaimPolicy(ManageTest):
    """
    Automates the following test cases
     OCS-383 - OCP_Validate Retain policy is honored
     OCS-384 - OCP_Validate Delete policy is honored
    """

    @pytest.mark.polarion_id("OCS-383")
    def test_reclaim_policy_retain(self):
        """
        Calling functions for pvc invalid name and size
        """
        pvc_count = len(list_ceph_images())
        pvc_obj = helpers.create_pvc(
            sc_name=self.sc_obj_retain.name,
            pvc_name=helpers.create_unique_resource_name('retain', 'pvc'))
        pv_name = pvc_obj.get()['spec']['volumeName']
        pv_namespace = pvc_obj.get()['metadata']['namespace']
        pv_obj = ocp.OCP(kind='PersistentVolume', namespace=pv_namespace)
        assert pvc_obj.delete()
        pvc_obj.ocp.wait_for_delete(resource_name=pvc_obj.name)
        assert pv_obj.get(pv_name).get('status').get('phase') == 'Released', (
            f"Status of PV {pv_obj.get(pv_name)} is not 'Released'"
        )
        log.info("Status of PV is Released")
        assert pvc_count + 1 == len(list_ceph_images())
        assert pv_obj.delete(resource_name=pv_name)
        # TODO: deletion of ceph rbd image, blocked by BZ#1723656

    @pytest.mark.polarion_id("OCS-384")
    def test_reclaim_policy_delete(self):
        """
        Test to validate storage class with reclaim policy "Delete"
        """
        pvc_obj = helpers.create_pvc(
            sc_name=self.sc_obj_delete.name,
            pvc_name=helpers.create_unique_resource_name('delete', 'pvc'))
        pv_name = pvc_obj.get()['spec']['volumeName']
        pv_namespace = pvc_obj.get()['metadata']['namespace']
        pv_obj = ocp.OCP(kind='PersistentVolume', namespace=pv_namespace)
        assert pvc_obj.delete()
        pvc_obj.ocp.wait_for_delete(resource_name=pvc_obj.name)
        try:
            pv_obj.get(pv_name)
        except CommandFailed as ex:
            assert f'persistentvolumes "{pv_name}" not found' in str(ex),\
                "pv exists"
            log.info("Underlying PV is deleted")
        # TODO: deletion of ceph rbd image, blocked by BZ#1723656
