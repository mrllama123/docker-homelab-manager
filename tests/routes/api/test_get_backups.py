from src.models import Backups


def test_get_backups(client, session):
    for backup_id in ["test-backup-id-1", "test-backup-id-2"]:
        session.add(
            Backups(
                backup_id=backup_id,
                created_at="2021-01-01T00:00:00+00:00",
                backup_filename=f"{backup_id}.tar.gz",
                backup_name="test-backup-name",
                successful=True,
                backup_path="/volumes/backup/test-backup-name.tar.gz",
                volume_name="test-volume",
            )
        )
    session.commit()
    response = client.get("/api/volumes/backup")
    assert response.status_code == 200
    assert response.json() == {
        "backups": [
            {
                "schedule_id": None,
                "backup_filename": "test-backup-id-1.tar.gz",
                "backup_id": "test-backup-id-1",
                "backup_path": "/volumes/backup/test-backup-name.tar.gz",
                "volume_name": "test-volume",
                "successful": True,
                "error_message": None,
                "backup_name": "test-backup-name",
                "created_at": "2021-01-01T00:00:00+00:00",
            },
            {
                "schedule_id": None,
                "backup_filename": "test-backup-id-2.tar.gz",
                "backup_id": "test-backup-id-2",
                "successful": True,
                "error_message": None,
                "backup_path": "/volumes/backup/test-backup-name.tar.gz",
                "backup_name": "test-backup-name",
                "volume_name": "test-volume",
                "created_at": "2021-01-01T00:00:00+00:00",
            },
        ],
        "page": 1,
        "size": 100,
        "total_items": 2,
        "total_pages": 1,
    }


def test_get_backups_paginated(client, session):
    for backup_id in [
        "test-backup-id-1",
        "test-backup-id-2",
        "test-backup-id-3",
        "test-backup-id-4",
        "test-backup-id-5",
    ]:
        session.add(
            Backups(
                backup_id=backup_id,
                created_at="2021-01-01T00:00:00+00:00",
                backup_filename=f"{backup_id}.tar.gz",
                backup_name="test-backup-name",
                successful=True,
                backup_path="/volumes/backup/test-backup-name.tar.gz",
                volume_name="test-volume",
            )
        )
    session.commit()

    # first page
    response = client.get("/api/volumes/backup?page=1&size=2")
    assert response.status_code == 200
    assert response.json() == {
        "backups": [
            {
                "schedule_id": None,
                "backup_filename": "test-backup-id-1.tar.gz",
                "backup_id": "test-backup-id-1",
                "backup_path": "/volumes/backup/test-backup-name.tar.gz",
                "volume_name": "test-volume",
                "successful": True,
                "error_message": None,
                "backup_name": "test-backup-name",
                "created_at": "2021-01-01T00:00:00+00:00",
            },
            {
                "schedule_id": None,
                "backup_filename": "test-backup-id-2.tar.gz",
                "backup_id": "test-backup-id-2",
                "successful": True,
                "error_message": None,
                "backup_path": "/volumes/backup/test-backup-name.tar.gz",
                "backup_name": "test-backup-name",
                "volume_name": "test-volume",
                "created_at": "2021-01-01T00:00:00+00:00",
            },
        ],
        "page": 1,
        "size": 2,
        "total_items": 5,
        "total_pages": 3,
    }
    assert (
        response.headers["link"]
        == '<http://testserver/api/volumes/backup?page=2&size=2>; rel="next", <http://testserver/api/volumes/backup?page=3&size=2>; rel="last"'
    )

    # second page
    response = client.get("/api/volumes/backup?page=2&size=2")
    assert response.status_code == 200
    assert response.json() == {
        "backups": [
            {
                "schedule_id": None,
                "backup_filename": "test-backup-id-3.tar.gz",
                "backup_id": "test-backup-id-3",
                "backup_path": "/volumes/backup/test-backup-name.tar.gz",
                "volume_name": "test-volume",
                "successful": True,
                "error_message": None,
                "backup_name": "test-backup-name",
                "created_at": "2021-01-01T00:00:00+00:00",
            },
            {
                "schedule_id": None,
                "backup_filename": "test-backup-id-4.tar.gz",
                "backup_id": "test-backup-id-4",
                "successful": True,
                "error_message": None,
                "backup_path": "/volumes/backup/test-backup-name.tar.gz",
                "backup_name": "test-backup-name",
                "volume_name": "test-volume",
                "created_at": "2021-01-01T00:00:00+00:00",
            },
        ],
        "page": 2,
        "size": 2,
        "total_items": 5,
        "total_pages": 3,
    }
    assert (
        response.headers["link"]
        == '<http://testserver/api/volumes/backup?page=3&size=2>; rel="next", <http://testserver/api/volumes/backup?page=1&size=2>; rel="prev", <http://testserver/api/volumes/backup?page=3&size=2>; rel="last"'
    )

    # third page
    response = client.get("/api/volumes/backup?page=3&size=2")
    assert response.status_code == 200
    assert response.json() == {
        "backups": [
            {
                "schedule_id": None,
                "backup_filename": "test-backup-id-5.tar.gz",
                "backup_id": "test-backup-id-5",
                "backup_path": "/volumes/backup/test-backup-name.tar.gz",
                "volume_name": "test-volume",
                "successful": True,
                "error_message": None,
                "backup_name": "test-backup-name",
                "created_at": "2021-01-01T00:00:00+00:00",
            }
        ],
        "page": 3,
        "size": 2,
        "total_items": 5,
        "total_pages": 3,
    }
    assert (
        response.headers["link"]
        == '<http://testserver/api/volumes/backup?page=1&size=2>; rel="first", <http://testserver/api/volumes/backup?page=3&size=2>; rel="last"'
    )


def test_get_no_backups(client):
    response = client.get("/api/volumes/backup")
    assert response.status_code == 200
    assert response.json() == {
        "backups": [],
        "page": 1,
        "size": 100,
        "total_items": 0,
        "total_pages": 1,
    }


def test_get_backup(client, session):
    session.add(
        Backups(
            backup_id="test-backup-id",
            backup_filename="test-backup-name.tar.gz",
            backup_name="test-backup-name",
            created_at="2021-01-01T00:00:00+00:00",
            successful=True,
            backup_path="/volumes/backup/test-backup-name.tar.gz",
            volume_name="test-volume",
        )
    )
    session.commit()
    response = client.get("/api/volumes/backup/test-backup-id")
    assert response.status_code == 200
    assert response.json() == {
        "backup_id": "test-backup-id",
        "backup_filename": "test-backup-name.tar.gz",
        "created_at": "2021-01-01T00:00:00+00:00",
        "backup_name": "test-backup-name",
        "successful": True,
        "error_message": None,
        "backup_path": "/volumes/backup/test-backup-name.tar.gz",
        "volume_name": "test-volume",
        "schedule_id": None,
    }
