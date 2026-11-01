import copy
import hashlib
import unittest
from imperial_plugins.llamafactory_adapter import (
    REFERENCE_MODEL, SYNTHETIC_RIGHTS, prepare_velion_finetune_plan
)

def row(i):
    return {
        "instruction": f"Return the smallest of the two integers, case {i}.",
        "input": f"a={i}, b={i+2}", "output": f"{i}",
        "source_id": f"synthetic:case-{i:03d}",
        "source_rights": SYNTHETIC_RIGHTS,
        "data_class": "PUBLIC_SYNTHETIC",
    }

def policy(**changes):
    return {
        "tenant_id": "imperial-internal", "orchestrator_id": "engineering-orch",
        "base_model_id": REFERENCE_MODEL,
        "base_model_revision": "1" * 40,
        "training_method": "QLORA",
        "manual_model_license_review_sha256": "a" * 64,
        "privacy_review_claimed": True, "gpu_budget_usd": 0,
        "model_download_permitted": False, **changes
    }

def planned(train=None, holdout=None, config=None):
    return prepare_velion_finetune_plan(
        [row(1), row(2)] if train is None else train,
        [row(3), row(4)] if holdout is None else holdout,
        policy() if config is None else config)

class TestVELIONLlamaFactoryAdapter(unittest.TestCase):
    def test_generates_offline_qlora_sft_alpaca_plan(self):
        p = planned()
        self.assertEqual(p["schema"], "imperial.velion.llamafactory.offline-plan.v1")
        self.assertEqual(p["training_examples"], 2)
        self.assertEqual(p["heldout_examples"], 2)
        self.assertIn("quantization_bit: 4", p["files"]["train.yaml"])
        self.assertIn("model_revision: " + "1" * 40, p["files"]["train.yaml"])
        self.assertIn("eval_dataset: imperial_eval", p["files"]["train.yaml"])
        self.assertIn("trust_remote_code: false", p["files"]["train.yaml"])
        self.assertIn("report_to: none", p["files"]["train.yaml"])
        self.assertNotIn("true\n", p["files"]["train.yaml"].split("trust_remote_code: ")[1].splitlines()[0])
        for filename, text in p["files"].items():
            digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
            self.assertEqual(p["file_sha256"][filename], digest)
        for name in ("training_invoked", "model_downloaded", "gpu_allocated",
                     "training_authorized", "independent_evaluation_verified",
                     "legal_rights_independently_verified", "model_weights_changed",
                     "owner_production_approval_verified", "external_effects"):
            self.assertFalse(p[name], name)
        self.assertEqual(p["cost_usd"], 0)
        self.assertTrue(p["release_blockers"])

    def test_lora_has_no_quantization(self):
        p = planned(config=policy(training_method="LORA"))
        self.assertNotIn("quantization_bit:", p["files"]["train.yaml"])
        self.assertNotIn("quantization_method:", p["files"]["train.yaml"])

    def test_repeatable_output(self):
        a = planned()
        b = planned()
        self.assertEqual(a, b)

    def test_no_provenance_published_in_training_payload(self):
        p = planned()
        for name in ("train.json", "eval.json"):
            self.assertNotIn("source_id", p["files"][name])
            self.assertNotIn("source_rights", p["files"][name])
            self.assertNotIn("data_class", p["files"][name])

    def test_dataset_info_matches_alpaca_standard(self):
        import json
        p = planned()
        info = json.loads(p["files"]["dataset_info.json"])
        self.assertEqual(info["imperial_train"]["file_name"], "train.json")
        self.assertEqual(info["imperial_train"]["columns"]["prompt"], "instruction")
        self.assertEqual(info["imperial_eval"]["columns"]["response"], "output")
        self.assertEqual(len(json.loads(p["files"]["train.json"])), 2)

    def test_rejects_leakage_by_prompt_including_case_fold(self):
        bad = row(3)
        bad["instruction"] = row(1)["instruction"].upper()
        bad["input"] = row(1)["input"].upper()
        with self.assertRaisesRegex(ValueError, "TRAIN_EVAL_PROMPT_LEAKAGE"):
            planned(holdout=[bad, row(4)])

    def test_rejects_overlap_by_source(self):
        bad = row(4)
        bad["source_id"] = "synthetic:case-001"
        with self.assertRaisesRegex(ValueError, "TRAIN_EVAL_SOURCE_LEAKAGE"):
            planned(holdout=[row(3), bad])

    def test_no_duplicate_train_prompt(self):
        bad = row(2)
        bad["instruction"] = row(1)["instruction"]
        bad["input"] = row(1)["input"]
        with self.assertRaisesRegex(ValueError, "DUPLICATE_PROMPT_WITHIN_SPLIT"):
            planned(train=[row(1), bad])

    def test_no_duplicate_source_in_split(self):
        bad = row(2)
        bad["source_id"] = row(1)["source_id"]
        with self.assertRaisesRegex(ValueError, "DATA_PROVENANCE_OR_CLASS_DENIED"):
            planned(train=[row(1), bad])

    def test_privacy_and_secret_negative_examples(self):
        for addition in ("contact me at test@example.com",
                         "-----BEGIN PRIVATE KEY-----",
                         "ghp_" + "A" * 35,
                         "sk-proj-" + "A" * 35,
                         "AKIA1234567890ABCDEF"):
            bad = row(1)
            bad["input"] += addition
            with self.subTest(sensitive=addition[:15]), self.assertRaisesRegex(
                    ValueError, "POSSIBLE_SECRET_OR_PERSONAL_DATA"):
                planned(train=[bad, row(2)])

    def test_policy_zero_trust_and_model_pin(self):
        changes = [
            {"base_model_id": "unreviewed/remote-model"},
            {"base_model_revision": "main"},
            {"base_model_revision": "0"*40},
            {"manual_model_license_review_sha256": ""},
            {"training_method": "FULL"},
            {"gpu_budget_usd": 1},
            {"gpu_budget_usd": True},
            {"model_download_permitted": True},
            {"privacy_review_claimed": False},
            {"tenant_id": "../other"},
            {"orchestrator_id": "bad:route!"}
        ]
        for bad in changes:
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                planned(config=policy(**bad))

    def test_untrusted_unhashable_inputs_denied(self):
        changes = [{"training_method": []}, {"base_model_id": []},
                   {"privacy_review_claimed": []}, {"manual_model_license_review_sha256": []},
                   {"model_download_permitted": []}]
        for bad in changes:
            with self.subTest(bad=bad), self.assertRaises((ValueError, TypeError)):
                planned(config=policy(**bad))

    def test_unknown_policy_fields_denied(self):
        with self.assertRaisesRegex(ValueError, "TRAINING_POLICY_SCHEMA_DENIED"):
            planned(config=policy(execute=True))

    def test_no_customer_or_proprietary_content(self):
        for name, value in (("data_class", "PRIVATE_CUSTOMER"),
                            ("source_rights", "UNLICENSED_WEB_SCRAPE"),
                            ("source_id", "https://unknown.site")):
            bad = row(1)
            bad[name] = value
            with self.subTest(name=name), self.assertRaises(ValueError):
                planned(train=[bad, row(2)])

    def test_dataset_size_and_structure_gate(self):
        for rows in ([], [{}], ["bad", row(2)], [row(1)],
                     [row(1)|{"url":"remote"}, row(2)]):
            with self.subTest(rows=rows),self.assertRaises(ValueError):
                planned(train=rows)

    def test_control_characters_and_overlong_rejected(self):
        for badinput in ("x\0y", "y"*4097):
            bad = row(1)
            bad["instruction"] = badinput
            with self.assertRaises(ValueError):
                planned(train=[bad, row(2)])

    def test_policy_object_not_modified(self):
        p = policy()
        old = copy.deepcopy(p)
        planned(config=p)
        self.assertEqual(p, old)

if __name__=="__main__":
    unittest.main()
