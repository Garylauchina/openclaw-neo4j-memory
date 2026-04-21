from pathlib import Path

from minimal_memory_kernel import MinimalMemoryStore, should_write_memory


def test_should_write_memory_filters_trivial_acknowledgements():
    assert should_write_memory("ok") is False
    assert should_write_memory("thanks") is False
    assert should_write_memory("This is a real memory candidate") is True


def test_minimal_memory_store_write_and_readback(tmp_path: Path):
    store = MinimalMemoryStore(tmp_path / "raw_memory.json")

    memory = store.write(
        source="telegram",
        content="User prefers concise answers about memory architecture.",
        context={"chat_id": "telegram:1"},
        metadata={"kind": "preference"},
    )

    assert memory is not None
    loaded = store.get(memory.id)
    assert loaded is not None
    assert loaded.content == "User prefers concise answers about memory architecture."
    assert loaded.source == "telegram"
    assert loaded.context["chat_id"] == "telegram:1"
    assert loaded.metadata["kind"] == "preference"


def test_recent_returns_latest_memories_first(tmp_path: Path):
    store = MinimalMemoryStore(tmp_path / "raw_memory.json")

    store.write(source="src", content="First meaningful memory.")
    store.write(source="src", content="Second meaningful memory.")
    recent = store.recent(limit=2)

    assert len(recent) == 2
    assert recent[0].content == "Second meaningful memory."
    assert recent[1].content == "First meaningful memory."
