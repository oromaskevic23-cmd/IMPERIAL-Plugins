"""Deterministic adversarial tests for public SEO-NCA practice exam."""
import unittest

from imperial_plugins.seo_nca_exam import (
    ACTIONS, CASES, SEOExamError, VERSION, evaluate, exam_outline,
)


def correct():
    return {"agent_id": "NCA-SEO-001", "exam_version": VERSION,
            "simulation_only": True,
            "answers": {name: answer for name, _, answer, _ in CASES}}


class SEOExamTests(unittest.TestCase):
    def test_complete_correct_practice_does_not_grant_access(self):
        r = evaluate(correct())
        self.assertEqual(r["status"], "PRACTICE_PASS")
        self.assertEqual(r["score_percent"], 100)
        self.assertEqual(r["total_cases"], 14)
        for key in ("independent_qa_verified", "production_skill_granted",
                    "ai_passport_issued", "google_api_access_granted",
                    "real_nca_model_invoked"):
            self.assertIs(r[key], False)

    def test_public_exam_source_and_choices_are_explicit(self):
        data = exam_outline()
        self.assertEqual(len(data["cases"]), 14)
        self.assertTrue(all(c["choices"] == sorted(ACTIONS) for c in data["cases"]))
        self.assertEqual(data["source"], "PUBLIC_PRACTICE_DATASET")
        self.assertFalse(data["production_skill_granted"])

    def test_critical_bypass_fails_even_at_high_score(self):
        c = correct()
        c["answers"]["indexing_api_misuse"] = "READ_ONLY"
        r = evaluate(c)
        self.assertEqual(r["status"], "PRACTICE_FAIL")
        self.assertIn("indexing_api_misuse", r["critical_failures"])
        self.assertGreaterEqual(r["score_percent"], 90)

    def test_one_noncritical_error_allowed_as_practice_only(self):
        c = correct()
        c["answers"]["canonical_audit"] = "PREPARE_REVIEW"
        r = evaluate(c)
        self.assertEqual(r["status"], "PRACTICE_PASS")
        self.assertEqual(r["critical_failures"], [])
        self.assertFalse(r["production_skill_granted"])

    def test_missing_extra_and_untrusted_answers_denied(self):
        for patch in ({"unknown": "DENY"},
                      {"indexing_api_misuse": "EXECUTE"},
                      {"oauth_scopes": {"exfiltrate": "token"}}):
            c = correct()
            c["answers"].update(patch)
            with self.subTest(patch=patch), self.assertRaises(SEOExamError):
                evaluate(c)

    def test_removed_case_denied(self):
        c = correct()
        del c["answers"]["host_robots"]
        with self.assertRaises(SEOExamError):
            evaluate(c)

    def test_malformed_identity_denied(self):
        for agent in ("owner", "../../../admin", "", None, "NCA-"):
            c = correct()
            c["agent_id"] = agent
            with self.subTest(agent=agent), self.assertRaises(SEOExamError):
                evaluate(c)

    def test_never_accept_production_or_unreviewed_version(self):
        for patch in ({"simulation_only": False}, {"exam_version": "2.0.0"},
                      {"authority": "GOOGLE_INDEXED"}):
            c = correct()
            c.update(patch)
            with self.subTest(patch=patch), self.assertRaises(SEOExamError):
                evaluate(c)

    def test_kill_switch_denies_even_perfect_answers(self):
        with self.assertRaisesRegex(SEOExamError, "OWNER_KILL_SWITCH"):
            evaluate(correct(), kill_switch=True)

    def test_incorrect_answer_hash_differs(self):
        a = evaluate(correct())
        c = correct()
        c["answers"]["canonical_audit"] = "DENY"
        b = evaluate(c)
        self.assertNotEqual(a["answer_sha256"], b["answer_sha256"])


if __name__ == "__main__":
    unittest.main()
