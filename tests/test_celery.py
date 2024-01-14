import pytest


# def get_redis_url(redis_client):
#     connection_info = redis_client.connection_pool.connection_kwargs
#     return f"redis://{connection_info['host']}:{connection_info['port']}"


# @pytest.fixture(scope='session')
# def celery_config(redisdb):
#     return {
#         'broker_url': get_redis_url(redisdb),
#         'result_backend': get_redis_url(redisdb)
#     }


# @pytest.fixture(scope='session')
# def celery_includes():
#     return [
#         'src.celery.worker',
#     ]

def test_sucessful_docker_backup_restore_task(celery_app, celery_worker, mocker):
    docker_client = mocker.patch("src.docker.DockerClient")
    session = mocker.patch(
        "src.docker.Session", **{"return_value.__enter__.return_value": mocker.Mock()}
    )
    mocker.patch("src.docker.select")
    from src.celery.worker import restore_volume_task

    # celery_worker.reload()

    restore_volume_task.delay("test-volume", "test-backup.tar.gz")
