import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import os
from processors import file_organizer_processor as fop

def test_scan_for_duplicates(tmp_path):
    a = tmp_path / "a.txt"
    b = tmp_path / "b.txt"
    c = tmp_path / "c.txt"
    a.write_text("same")
    b.write_text("same")
    c.write_text("diff")
    conn = fop._get_db(str(tmp_path / "cache.db"))
    dupes = fop.scan_for_duplicates([str(tmp_path)], recursive=False, conn=conn)
    # Expect one group of duplicates containing a and b
    values = list(dupes.values())
    assert any({str(a), str(b)} <= set(group) for group in values)

