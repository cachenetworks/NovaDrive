from __future__ import annotations

import tempfile
from collections.abc import Generator
from typing import BinaryIO


class ChunkValidationError(ValueError):
    pass


def calculate_safe_chunk_size(limit_bytes: int, margin_bytes: int) -> int:
    return max(1, limit_bytes - margin_bytes)


def iter_file_chunks(stream: BinaryIO, chunk_size: int) -> Generator[tuple[int, bytes], None, None]:
    index = 0
    while True:
        chunk = stream.read(chunk_size)
        if not chunk:
            break
        yield index, chunk
        index += 1


def spooled_temp_copy(source_stream: BinaryIO, max_memory_bytes: int) -> tempfile.SpooledTemporaryFile:
    temp_file = tempfile.SpooledTemporaryFile(max_size=max_memory_bytes, mode="w+b")
    while True:
        data = source_stream.read(1024 * 1024)
        if not data:
            break
        temp_file.write(data)
    temp_file.seek(0)
    return temp_file


def validate_chunk_indexes(indexes: list[int], expected_total: int) -> None:
    if len(indexes) != expected_total:
        raise ChunkValidationError("Chunk count mismatch for file manifest.")
    if sorted(indexes) != list(range(expected_total)):
        raise ChunkValidationError("Chunk ordering is incomplete or out of sequence.")

