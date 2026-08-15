import pytest
from agent.runtime.event_bus import EventType, RuntimeEvent, RuntimeEventBus


@pytest.fixture
def bus() -> RuntimeEventBus:
    return RuntimeEventBus()


@pytest.mark.asyncio
async def test_event_publishing_and_sequence(bus: RuntimeEventBus):
    event1 = await bus.publish(
        event_type=EventType.SESSION_STARTED,
        session_id="sess-100",
        payload={"goal": "refactor code"},
    )

    event2 = await bus.publish(
        event_type=EventType.ACTION_PROPOSED,
        session_id="sess-100",
        payload={"tool_name": "fs.write_file"},
        action_id="act-001",
        correlation_id="corr-999",
    )

    assert event1.sequence_number == 1
    assert event2.sequence_number == 2
    assert event2.session_id == "sess-100"
    assert event2.action_id == "act-001"
    assert event2.correlation_id == "corr-999"

    events = bus.get_events("sess-100")
    assert len(events) == 2
    assert events[0].event_type == EventType.SESSION_STARTED
    assert events[1].event_type == EventType.ACTION_PROPOSED


@pytest.mark.asyncio
async def test_event_handlers_and_subscribers(bus: RuntimeEventBus):
    received_specific = []
    received_global = []

    def sync_handler(evt: RuntimeEvent):
        received_specific.append(evt)

    async def async_global_handler(evt: RuntimeEvent):
        received_global.append(evt)

    bus.subscribe(EventType.CHECKPOINT_CREATED, sync_handler)
    bus.subscribe_all(async_global_handler)

    await bus.publish(EventType.SESSION_STARTED, "sess-1", {"status": "started"})
    await bus.publish(EventType.CHECKPOINT_CREATED, "sess-1", {"chk_id": "chk-1"})

    assert len(received_specific) == 1
    assert received_specific[0].event_type == EventType.CHECKPOINT_CREATED

    assert len(received_global) == 2
    assert received_global[0].event_type == EventType.SESSION_STARTED
    assert received_global[1].event_type == EventType.CHECKPOINT_CREATED


@pytest.mark.asyncio
async def test_event_json_serialization(bus: RuntimeEventBus):
    event = await bus.publish(
        event_type=EventType.ACTION_COMMITTED,
        session_id="sess-200",
        payload={"status": "COMMITTED"},
        action_id="act-555",
    )

    json_str = event.model_dump_json()
    assert '"event_type":"ACTION_COMMITTED"' in json_str
    assert '"session_id":"sess-200"' in json_str
    assert '"action_id":"act-555"' in json_str
