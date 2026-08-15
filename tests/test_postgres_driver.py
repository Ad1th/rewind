import pytest

from agent.execution.postgres import PostgresRollbackDriver, PostgresDriverError


@pytest.fixture
def db_driver() -> PostgresRollbackDriver:
    return PostgresRollbackDriver()


@pytest.mark.asyncio
async def test_postgres_insert_and_inverse_restore(db_driver: PostgresRollbackDriver):
    res, preimage_id = db_driver.insert_row(
        table_name="users",
        primary_key="id",
        row_data={"id": 1, "username": "alice", "role": "admin"},
    )
    assert res.success is True
    assert db_driver._tables["users"][1]["username"] == "alice"

    # Restore preimage
    restored = db_driver.restore_row_preimage(preimage_id)
    assert restored is True
    assert 1 not in db_driver._tables.get("users", {})


@pytest.mark.asyncio
async def test_postgres_update_and_delete_restoration(db_driver: PostgresRollbackDriver):
    # Insert initial row
    db_driver.insert_row("users", "id", {"id": 2, "username": "bob", "email": "bob@old.com"})

    # Update row
    res_upd, preimage_upd = db_driver.update_row("users", "id", 2, {"email": "bob@new.com"})
    assert res_upd.success is True
    assert db_driver._tables["users"][2]["email"] == "bob@new.com"

    # Delete row
    res_del, preimage_del = db_driver.delete_row("users", "id", 2)
    assert res_del.success is True
    assert 2 not in db_driver._tables["users"]

    # Restore deletion -> Row recreated
    db_driver.restore_row_preimage(preimage_del)
    assert db_driver._tables["users"][2]["email"] == "bob@new.com"

    # Restore update -> Row email reset to bob@old.com
    db_driver.restore_row_preimage(preimage_upd)
    assert db_driver._tables["users"][2]["email"] == "bob@old.com"


@pytest.mark.asyncio
async def test_postgres_savepoint_rollback(db_driver: PostgresRollbackDriver):
    db_driver.insert_row("users", "id", {"id": 10, "username": "charlie"})
    savepoint_name = await db_driver.capture_snapshot("sess-1", step_index=1)

    db_driver.insert_row("users", "id", {"id": 11, "username": "dave"})
    assert 11 in db_driver._tables["users"]

    db_driver.rollback_savepoint(savepoint_name)
    assert 10 in db_driver._tables["users"]
    assert 11 not in db_driver._tables["users"]
