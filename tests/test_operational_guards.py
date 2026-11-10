"""Synthetic-only regression fixtures; no provider access or camera streams."""
import unittest
from imperial_plugins.render_resource_guard import assess_render_events
from imperial_plugins.mission_truth_gate import assess_nca_readiness
from imperial_plugins.camera_rights_preflight import preflight_camera_source

NOW = "2026-11-10T10:30:00Z"


def oom(at, limit="512Mi"):
    return {"timestamp": at, "type": "server_failed",
            "details": {"reason": {"oomKilled": {"memoryLimit": limit}}}}


def readiness():
    return {"nca": {"checked_at": "2026-11-10T10:25:00Z",
                    "cron_healthy": 3, "cron_expected": 3,
                    "observed_model_processes": 0, "production_authorized": False},
            "worker": {"state": "APPROVAL_EXPIRED", "runtime_processes": 0,
                       "owner_kill_switch": False,
                       "approval_expires_at": "2026-10-31T14:44:00Z"},
            "crm": {"live_workers": 0, "active_jobs": 0},
            "gate": {"gate_state": "PENDING", "owner_signature_verified": False,
                     "independent_qa_verified": False}}


def camera():
    return {"source_id": "fixture01", "tenant_id": "tenant01",
            "source_type": "SYNTHETIC", "rights_reference": "fixtureRight01",
            "expires_at": "2026-11-11T00:00:00Z", "purpose": "camera_health",
            "event_types": ["signal_loss"], "retention_seconds": 0}


class TestRenderGuard(unittest.TestCase):
    def test_repeat_oom_even_if_available_after(self):
        events = [oom("2026-11-10T09:00:00Z"),
                  {"timestamp": "2026-11-10T09:10:00Z", "type": "server_available"},
                  oom("2026-11-10T10:00:00Z"),
                  {"timestamp": "2026-11-10T10:10:00Z", "type": "server_available"}]
        result = assess_render_events("render-test", events, now=NOW)
        self.assertEqual(result["status"], "REPEATED_OOM")
        self.assertEqual(result["oom_events"], 2)
        self.assertFalse(result["recovery_authorized"])
        self.assertFalse(result["production_health_verified"])

    def test_missing_events_not_healthy(self):
        result = assess_render_events("render-test", [], now=NOW)
        self.assertEqual(result["status"], "INSUFFICIENT_FRESH_EVENTS")

    def test_empty_reason_does_not_throw(self):
        a = assess_render_events("render-test", [{"timestamp": NOW, "type": "server_failed"}], now=NOW)
        self.assertEqual(a["status"], "NO_OOM_IN_PROVIDED_WINDOW")
        self.assertFalse(a["production_health_verified"])

    def test_future_timestamp_refused(self):
        with self.assertRaisesRegex(ValueError, "FUTURE_EVENT"):
            assess_render_events("render-test", [oom("2026-11-11T00:00:00Z")], now=NOW)

    def test_secret_like_id_refused(self):
        with self.assertRaisesRegex(ValueError, "INVALID_SERVICE_ID"):
            assess_render_events("https://user:pass@invalid/", [], now=NOW)

    def test_oversized_batch_refused(self):
        with self.assertRaisesRegex(ValueError, "INVALID_EVENT_BATCH"):
            assess_render_events("render-test", [{}] * 501, now=NOW)


class TestTruthGate(unittest.TestCase):
    def test_current_nca_evidence_is_not_production(self):
        r = assess_nca_readiness(readiness(), now=NOW)
        self.assertIn("OWNER_APPROVAL_EXPIRED", r["blockers"])
        self.assertIn("NO_MODEL_WORKER_PROCESS", r["blockers"])
        self.assertFalse(r["execution_authorized"])
        self.assertEqual(r["stage"], "BLOCKED_OR_LAB_ONLY")

    def test_all_self_attested_green_never_grants_execution(self):
        x = readiness()
        x["worker"].update({"state": "RUNNING", "runtime_processes": 1,
                            "approval_expires_at": "2026-11-12T00:00:00Z"})
        x["nca"].update({"observed_model_processes": 1, "production_authorized": True})
        x["crm"]["live_workers"] = 1
        x["gate"].update({"gate_state": "PASS", "owner_signature_verified": True,
                          "independent_qa_verified": True})
        r = assess_nca_readiness(x, now=NOW)
        self.assertEqual(r["stage"], "EXTERNAL_VERIFICATION_REQUIRED")
        self.assertFalse(r["production_ready_verified"])
        self.assertFalse(r["execution_authorized"])

    def test_stale_snapshot_and_kill_switch(self):
        x = readiness()
        x["nca"]["checked_at"] = "2026-11-09T00:00:00Z"
        x["worker"]["owner_kill_switch"] = True
        r = assess_nca_readiness(x, now=NOW)
        self.assertIn("OWNER_KILL_SWITCH_ACTIVE", r["blockers"])
        self.assertIn("STALE_RUNTIME_SNAPSHOT", r["blockers"])

    def test_boolean_as_worker_count_refused(self):
        x = readiness()
        x["crm"]["live_workers"] = True
        with self.assertRaisesRegex(ValueError, "INVALID_CRM_COUNT"):
            assess_nca_readiness(x, now=NOW)

    def test_missing_gate_refused(self):
        x = readiness()
        del x["gate"]
        with self.assertRaisesRegex(ValueError, "INVALID_READINESS_SCHEMA"):
            assess_nca_readiness(x, now=NOW)


class TestRightsPreflight(unittest.TestCase):
    def test_safe_synthetic_only_eligible_for_review(self):
        r = preflight_camera_source(camera(), now=NOW)
        self.assertTrue(r["eligible_for_external_review"])
        self.assertFalse(r["stream_connection_authorized"])
        self.assertFalse(r["production_authorized"])

    def test_unauthorized_tracking_denied(self):
        x = camera()
        x["event_types"] = ["face_search"]
        self.assertEqual(preflight_camera_source(x, now=NOW)["reason"], "PROHIBITED_EVENT_ANALYSIS")

    def test_password_url_cannot_appear(self):
        x = camera()
        x["camera_url"] = "rtsp://admin:secret@host/stream"
        self.assertEqual(preflight_camera_source(x, now=NOW)["reason"], "INVALID_SOURCE_SCHEMA")

    def test_expired_source_denied(self):
        x = camera()
        x["expires_at"] = "2026-11-09T00:00:00Z"
        self.assertEqual(preflight_camera_source(x, now=NOW)["reason"], "RIGHTS_EXPIRED")

    def test_public_metadata_cannot_be_archived(self):
        x = camera()
        x["source_type"] = "LICENSED_PUBLIC_METADATA"
        x["retention_seconds"] = 100
        self.assertEqual(preflight_camera_source(x, now=NOW)["reason"], "PUBLIC_METADATA_ARCHIVE_DENIED")

    def test_non_integer_retention_denied(self):
        x = camera()
        x["retention_seconds"] = False
        self.assertEqual(preflight_camera_source(x, now=NOW)["reason"], "INVALID_RETENTION_LIMIT")

    def test_unknown_rights_type_denied(self):
        x = camera()
        x["source_type"] = "GLOBAL_ACCESS"
        self.assertEqual(preflight_camera_source(x, now=NOW)["reason"], "UNRECOGNIZED_SOURCE_TYPE")

    def test_unhashable_rights_type_denied(self):
        x = camera()
        x["source_type"] = ["SYNTHETIC"]
        self.assertEqual(preflight_camera_source(x, now=NOW)["reason"], "UNRECOGNIZED_SOURCE_TYPE")


if __name__ == "__main__":
    unittest.main()
