import unittest
from main import evaluate

class GuardianTests(unittest.TestCase):
    def test_missing_passport(self):
        self.assertFalse(evaluate({"action":"read:public"})["allowed"])
    def test_denies_execution(self):
        self.assertFalse(evaluate({"action":"execute:payment","ai_passport":"nca-1","approval":True})["allowed"])
    def test_simulation_needs_approval(self):
        self.assertFalse(evaluate({"action":"simulate:task","ai_passport":"nca-1"})["allowed"])
    def test_public_read(self):
        self.assertTrue(evaluate({"action":"read:public","ai_passport":"nca-1"})["allowed"])

if __name__ == "__main__": unittest.main()
