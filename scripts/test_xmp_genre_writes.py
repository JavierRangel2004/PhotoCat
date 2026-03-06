"""
test_xmp_genre_writes.py — Unit tests for XMP genre write invariants.

Tests three invariants from the Phase 2 review contract:
  1. review_status == "skip"   → no genre tag written to XMP
  2. review_status == "review" → genre tag + "genre-needs-review" written
  3. review_status == "auto"   → genre tag only, no "genre-needs-review"

Does NOT require a real image or SigLIP2. Calls metadata_writer directly
with synthetic genre_result dicts.
"""

import os
import sys
import shutil
import tempfile
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from metadata_writer import write_xmp_sidecar

NAMESPACES = {
    "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    "dc":  "http://purl.org/dc/elements/1.1/",
    "xmp": "http://ns.adobe.com/xap/1.0/",
}


def _read_xmp_tags(xmp_path):
    """Return the list of dc:subject tags from an XMP sidecar."""
    tree = ET.parse(xmp_path)
    root = tree.getroot()
    tags = []
    for li in root.findall(".//dc:subject/rdf:Bag/rdf:li", NAMESPACES):
        if li.text:
            tags.append(li.text)
    return tags


def _make_fake_jpg(tmp_dir, name="test.jpg"):
    """Create a tiny valid JPEG stub (1×1 pixel) so write_xmp_sidecar can
    derive a sidecar path from it without needing a real image."""
    path = os.path.join(tmp_dir, name)
    # Minimal valid JPEG bytes (1×1 white pixel)
    jpeg_bytes = (
        b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00"
        b"\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t"
        b"\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a"
        b"\x1f\x1e\x1d\x1a\x1c\x1c $.' \",#\x1c\x1c(7),\x01\x01\x01\x01"
        b"\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\xff\xc0\x00"
        b"\x0b\x08\x00\x01\x00\x01\x01\x01\x11\x00\xff\xc4\x00\x1f\x00"
        b"\x00\x01\x05\x01\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00"
        b"\x00\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\xff\xd9"
    )
    with open(path, "wb") as f:
        f.write(jpeg_bytes)
    return path


def _run_write(tmp_dir, jpg_name, genre_result, base_tags=None):
    """Write a sidecar and return the list of tags in it."""
    jpg = _make_fake_jpg(tmp_dir, jpg_name)
    write_xmp_sidecar(
        jpg,
        rating=3,
        tags=base_tags or ["test-tag"],
        title="Test image.",
        genre_result=genre_result,
    )
    xmp_path = os.path.splitext(jpg)[0] + ".xmp"
    assert os.path.exists(xmp_path), f"XMP not created at {xmp_path}"
    return _read_xmp_tags(xmp_path)


# ──────────────────────────────────────────────────────────────────────────────
# Test cases
# ──────────────────────────────────────────────────────────────────────────────

def test_skip_does_not_write_genre():
    """review_status == 'skip' must NOT add any genre tag."""
    with tempfile.TemporaryDirectory() as tmp:
        genre_result = {
            "genre": "Concert Photography",
            "confidence": 0.40,
            "review_status": "skip",
        }
        tags = _run_write(tmp, "skip_test.jpg", genre_result)

    assert "Concert Photography" not in tags, (
        f"FAIL [skip]: genre tag must NOT be written, got tags={tags}"
    )
    assert "genre-needs-review" not in tags, (
        f"FAIL [skip]: review tag must NOT be written, got tags={tags}"
    )
    print("PASS  test_skip_does_not_write_genre")


def test_review_writes_genre_and_review_tag():
    """review_status == 'review' must write genre tag AND 'genre-needs-review'."""
    with tempfile.TemporaryDirectory() as tmp:
        genre_result = {
            "genre": "Street Photography",
            "confidence": 0.65,
            "review_status": "review",
        }
        tags = _run_write(tmp, "review_test.jpg", genre_result)

    assert "Street Photography" in tags, (
        f"FAIL [review]: genre tag must be written, got tags={tags}"
    )
    assert "genre-needs-review" in tags, (
        f"FAIL [review]: 'genre-needs-review' tag must be written, got tags={tags}"
    )
    print("PASS  test_review_writes_genre_and_review_tag")


def test_auto_writes_genre_only():
    """review_status == 'auto' must write genre tag but NOT 'genre-needs-review'."""
    with tempfile.TemporaryDirectory() as tmp:
        genre_result = {
            "genre": "Nature Photography",
            "confidence": 0.88,
            "review_status": "auto",
        }
        tags = _run_write(tmp, "auto_test.jpg", genre_result)

    assert "Nature Photography" in tags, (
        f"FAIL [auto]: genre tag must be written, got tags={tags}"
    )
    assert "genre-needs-review" not in tags, (
        f"FAIL [auto]: 'genre-needs-review' must NOT appear, got tags={tags}"
    )
    print("PASS  test_auto_writes_genre_only")


def test_none_genre_result_writes_no_genre():
    """Passing genre_result=None must not write any genre tag (backwards compat)."""
    with tempfile.TemporaryDirectory() as tmp:
        tags = _run_write(tmp, "none_test.jpg", genre_result=None, base_tags=["portrait"])

    assert "genre-needs-review" not in tags, (
        f"FAIL [none]: review tag must NOT appear, got tags={tags}"
    )
    # Base tag should still be present
    assert "portrait" in tags, (
        f"FAIL [none]: existing base tags must survive, got tags={tags}"
    )
    print("PASS  test_none_genre_result_writes_no_genre")


# ──────────────────────────────────────────────────────────────────────────────
# Runner
# ──────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    failures = []
    tests = [
        test_skip_does_not_write_genre,
        test_review_writes_genre_and_review_tag,
        test_auto_writes_genre_only,
        test_none_genre_result_writes_no_genre,
    ]
    for t in tests:
        try:
            t()
        except AssertionError as e:
            print(f"  {e}")
            failures.append(t.__name__)
        except Exception as e:
            print(f"ERROR in {t.__name__}: {e}")
            failures.append(t.__name__)

    print()
    if failures:
        print(f"FAILED: {failures}")
        sys.exit(1)
    else:
        print(f"All {len(tests)} tests passed. XMP genre write invariants verified.")
