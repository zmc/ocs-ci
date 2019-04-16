import logging
import random
import sys
log = logging.getLogger(__name__)


def run(**kw):
    ''' A task for radosbench

    '''
    log.info("Running radosbench task")
    ceph_pods = kw.get('ceph_pods')  # list of pod objects of ceph cluster
    config = kw.get('config')

    clients = []
    role = config.get('role', 'client')

    clients = [cpod for cpod in ceph_pods if role in cpod.roles]

    idx = config.get('idx', 0)
    client = clients[idx]
    pg_num = config.get('pg_num', 64)
    op = config.get('op', 'write')
    cleanup = ['--no-cleanup', '--cleanup'][config.get('cleanup', True)]
    pool = config.get('pool', 'test_pool' + str(random.randint(10, 999)))

    # FIXME: replace pool create with library function
    pool_create = "ceph osd pool create {pool_name} {pg_num}".format(
        pool_name=pool,
        pg_num=pg_num)
    out, err, ret = client.exec_command(cmd=pool_create,
                                        check_ec=True)
    if ret:
        log.error("Pool creation failed for {}".format(pool))
        log.error(err)
        return ret
    log.info("Pool {} created".format(pool))
    log.info(out)

    block = str(config.get('size', 4 << 20))
    time = config.get('time', 120)
    timeout = time + 10
    time = str(time)
    rados_bench = "rados --no-log-to-stderr -b {block} -p {pool} bench \
           {time} {op} {cleanup}".format(block=block, pool=pool, time=time,
                                         op=op, cleanup=cleanup)
    out, err, ret = client.exec_command(cmd=rados_bench,
                                        check_ec=True,
                                        long_running=True,
                                        timeout=timeout)
    if ret:
        log.error("Rados bench failed")
        log.error(err)
        return ret
    log.info(out)
    log.info("Finished radosbench")
    return ret
