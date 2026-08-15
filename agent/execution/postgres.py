"""PostgreSQL Transactional & Row Pre-Image Inverse Driver."""

import copy
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4
from pydantic import BaseModel, ConfigDict, Field

from agent.runtime.checkpoint import PostgresSnapshotProvider
from agent.runtime.contracts import ActionResult, InverseOperationReference


class PostgresDriverError(Exception):
    """Base exception for PostgreSQL Driver operations."""
    pass


class RowPreimage(BaseModel):
    """Pre-execution image of a database row."""

    table_name: str
    primary_key: str
    primary_key_value: Any
    data: Optional[Dict[str, Any]] = None  # None if row did not exist prior to INSERT

    model_config = ConfigDict(frozen=True)


class PostgresRollbackDriver(PostgresSnapshotProvider):
    """Executes database mutations, captures row pre-images, and executes inverse queries or savepoint rollbacks."""

    def __init__(self) -> None:
        self._preimages: Dict[str, RowPreimage] = {}  # preimage_id -> RowPreimage
        self._tables: Dict[str, Dict[Any, Dict[str, Any]]] = {}  # table_name -> {pk_val: row_dict}
        self._savepoints: Dict[str, Dict[str, Dict[Any, Dict[str, Any]]]] = {}

    async def capture_snapshot(self, session_id: str, step_index: int) -> Optional[str]:
        """Capture savepoint name for transaction checkpointing."""
        savepoint_name = f"rewind_savepoint_step_{step_index}"
        # Snapshot current database state for savepoint
        self._savepoints[savepoint_name] = copy.deepcopy(self._tables)
        return savepoint_name

    def capture_row_preimage(
        self,
        table_name: str,
        primary_key: str,
        primary_key_value: Any,
    ) -> str:
        """Capture row state before mutation."""
        preimage_id = f"preimage_{uuid4().hex[:12]}"
        existing_row = self._tables.get(table_name, {}).get(primary_key_value)
        preimage = RowPreimage(
            table_name=table_name,
            primary_key=primary_key,
            primary_key_value=primary_key_value,
            data=dict(existing_row) if existing_row else None,
        )
        self._preimages[preimage_id] = preimage
        return preimage_id

    def insert_row(
        self,
        table_name: str,
        primary_key: str,
        row_data: Dict[str, Any],
    ) -> Tuple[ActionResult, str]:
        """Execute row insertion and return ActionResult + preimage_id."""
        pk_val = row_data[primary_key]
        preimage_id = self.capture_row_preimage(table_name, primary_key, pk_val)

        if table_name not in self._tables:
            self._tables[table_name] = {}
        self._tables[table_name][pk_val] = row_data

        return (
            ActionResult(
                success=True,
                output={"table": table_name, "primary_key": pk_val, "action": "INSERT"},
            ),
            preimage_id,
        )

    def update_row(
        self,
        table_name: str,
        primary_key: str,
        primary_key_value: Any,
        new_values: Dict[str, Any],
    ) -> Tuple[ActionResult, str]:
        """Execute row update and return ActionResult + preimage_id."""
        preimage_id = self.capture_row_preimage(table_name, primary_key, primary_key_value)
        if table_name not in self._tables or primary_key_value not in self._tables[table_name]:
            return (
                ActionResult(success=False, error_message=f"Row '{primary_key_value}' in '{table_name}' not found."),
                preimage_id,
            )

        self._tables[table_name][primary_key_value].update(new_values)
        return (
            ActionResult(
                success=True,
                output={"table": table_name, "primary_key": primary_key_value, "action": "UPDATE"},
            ),
            preimage_id,
        )

    def delete_row(
        self,
        table_name: str,
        primary_key: str,
        primary_key_value: Any,
    ) -> Tuple[ActionResult, str]:
        """Execute row deletion and return ActionResult + preimage_id."""
        preimage_id = self.capture_row_preimage(table_name, primary_key, primary_key_value)
        if table_name in self._tables and primary_key_value in self._tables[table_name]:
            del self._tables[table_name][primary_key_value]

        return (
            ActionResult(
                success=True,
                output={"table": table_name, "primary_key": primary_key_value, "action": "DELETE"},
            ),
            preimage_id,
        )

    def rollback_savepoint(self, savepoint_name: str) -> bool:
        """Rollback table state to exact savepoint snapshot."""
        if savepoint_name not in self._savepoints:
            raise PostgresDriverError(f"Savepoint '{savepoint_name}' not found.")
        self._tables = copy.deepcopy(self._savepoints[savepoint_name])
        return True

    def restore_row_preimage(self, preimage_id: str) -> bool:
        """Restore single row using captured pre-image."""
        if preimage_id not in self._preimages:
            raise PostgresDriverError(f"Preimage '{preimage_id}' not found.")

        preimage = self._preimages[preimage_id]
        table = preimage.table_name
        pk_val = preimage.primary_key_value

        if preimage.data is None:
            # Row was created during step -> Delete created row
            if table in self._tables and pk_val in self._tables[table]:
                del self._tables[table][pk_val]
        else:
            # Restore previous row values
            if table not in self._tables:
                self._tables[table] = {}
            self._tables[table][pk_val] = dict(preimage.data)

        return True

    def generate_inverse_recipe(
        self,
        operation: str,
        table_name: str,
        primary_key: str,
        primary_key_value: Any,
        preimage_id: str,
    ) -> InverseOperationReference:
        """Synthesize exact inverse recipe for database operations."""
        return InverseOperationReference(
            inverse_tool_name="db.restore_row_preimage",
            arguments={
                "operation": operation,
                "table_name": table_name,
                "primary_key": primary_key,
                "primary_key_value": primary_key_value,
                "preimage_id": preimage_id,
            },
        )
