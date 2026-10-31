import unittest
from main import chain_event

class LedgerTests(unittest.TestCase):
    def test_deterministic(self):
        a = chain_event("0" * 64, {"type": "task", "id": "1"})
        b = chain_event("0" * 64, {"id": "1", "type": "task"})
        self.assertEqual(a["hash"], b["hash"])
    def test_invalid_parent(self):
        with self.assertRaises(ValueError): chain_event("bad", {})

if __name__ == "__main__": unittest.main()
