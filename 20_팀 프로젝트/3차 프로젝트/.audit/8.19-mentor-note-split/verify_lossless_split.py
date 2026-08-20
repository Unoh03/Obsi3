#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

START_RE = re.compile(rb"<!-- 8\.19-MENTOR-SOURCE-BLOCK (B\d{3}) START -->")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git_blob_sha(data: bytes) -> str:
    header = f"blob {len(data)}\0".encode("ascii")
    return hashlib.sha1(header + data).hexdigest()


def repo_root() -> Path:
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return Path(result.stdout.decode("utf-8").strip())


def main() -> int:
    root = repo_root()
    audit_dir = Path(__file__).resolve().parent
    manifest = json.loads((audit_dir / "manifest.json").read_text(encoding="utf-8"))

    original = subprocess.run(
        ["git", "show", f"{manifest['source']['commit']}:{manifest['source']['path']}"],
        cwd=root,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    ).stdout

    errors: list[str] = []
    if len(original) != manifest["source"]["byte_length"]:
        errors.append("source byte length mismatch")
    if sha256(original) != manifest["source"]["sha256"]:
        errors.append("source SHA-256 mismatch")
    if git_blob_sha(original) != manifest["source"]["git_blob_sha"]:
        errors.append("source Git blob SHA mismatch")

    observed_ids: list[str] = []
    for destination in manifest["destination_files"]:
        data = (root / destination).read_bytes()
        observed_ids.extend(match.group(1).decode("ascii") for match in START_RE.finditer(data))

    expected_ids = [block["id"] for block in manifest["blocks"]]
    if sorted(observed_ids) != sorted(expected_ids):
        errors.append(f"source marker set mismatch: expected={expected_ids}, observed={observed_ids}")
    if len(observed_ids) != len(set(observed_ids)):
        errors.append("duplicate source block marker found")

    reconstructed_parts: list[bytes] = []
    for block in sorted(manifest["blocks"], key=lambda item: item["source_order"]):
        block_id = block["id"]
        destination = root / block["destination_file"]
        data = destination.read_bytes()
        start_marker = f"<!-- 8.19-MENTOR-SOURCE-BLOCK {block_id} START -->\n".encode("utf-8")
        end_marker = f"<!-- 8.19-MENTOR-SOURCE-BLOCK {block_id} END -->".encode("utf-8")
        if data.count(start_marker) != 1:
            errors.append(f"{block_id}: start marker count != 1")
            continue
        start = data.index(start_marker) + len(start_marker)
        length = block["byte_length"]
        payload = data[start : start + length]
        if len(payload) != length:
            errors.append(f"{block_id}: payload truncated")
            continue
        if sha256(payload) != block["sha256"]:
            errors.append(f"{block_id}: payload SHA-256 mismatch")
        suffix = data[start + length :]
        if not suffix.startswith(b"\n" + end_marker):
            errors.append(f"{block_id}: end marker not at expected byte boundary")
        reconstructed_parts.append(payload)

    reconstructed = b"".join(reconstructed_parts)
    if reconstructed != original:
        errors.append("reverse-assembled bytes do not equal source bytes")
    if sha256(reconstructed) != manifest["source"]["sha256"]:
        errors.append("reverse-assembled SHA-256 mismatch")

    if errors:
        print("RESULT: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1

    print("RESULT: PASS")
    print(f"Original blocks: {len(manifest['blocks'])}")
    print(f"Mapped blocks: {len(observed_ids)}")
    print("Unmapped blocks: 0")
    print("Duplicate source blocks: 0")
    print("Hash mismatches: 0")
    print(f"Original bytes: {len(original)}")
    print(f"Reconstructed bytes: {len(reconstructed)}")
    print(f"SHA-256: {sha256(reconstructed)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
