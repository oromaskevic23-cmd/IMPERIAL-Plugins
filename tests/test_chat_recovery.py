"""Offline ChatGPT recovery plugin tests; synthetic data only, no user's chats."""
import json
import os
import sqlite3
import tempfile
import unittest
from datetime import datetime,timezone
from pathlib import Path

from imperial_plugins.chat_recovery import (
    AGENTS, RecoveryError, build_index, recover, _redact, _date_limit,
)


def timestamp(s):
    return datetime.fromisoformat(s).replace(tzinfo=timezone.utc).timestamp()


def node(node_id, parent, text, when, role="user"):
    return {
        "id":node_id, "parent":parent, "children":[],
        "message": {"author":{"role":role}, "create_time":timestamp(when),
                    "content":{"content_type":"text","parts":[text]}}
    }


def export_fixture():
    # Simulates a branch where an earlier alternate draft must not be shown
    # as canonical even if it is chronologically before Val Town.
    return [{
        "id":"chat-main","title":"IMPERIAL Core HANTER architecture",
        "create_time":timestamp("2026-05-01"),
        "current_node":"c",
        "mapping":{
            "a":node("a",None,"HANTER Federated Multi-Orchestrator design created. Module proofgraph.", "2026-05-02"),
            "b":node("b","a","Val Town tested after original core planning.","2026-06-02"),
            "c":node("c","b","Astra controls specialized NCA subagents through HANTER.","2026-06-03",role="assistant"),
            "alt":node("alt","a","HANTER superseded alternate idea: global mega orchestrator.","2026-05-03"),
        }
    },{
        "id":"chat-secret","title":"PRIVATE FILES and credentials",
        "create_time":timestamp("2026-05-01"),
        "current_node":"secret",
        "mapping":{
            "secret":node("secret",None,
                "GitHub module: ghp_"+"A"*40+
                " account owner john@example.test bot 1234567890:AA"+"B"*40,
                "2026-05-04")
        }
    }]


class ChatRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix="imperial-chat-recovery-fixtures-")
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.export=self.root/"conversations.json"
        self.db=self.root/"private-search.sqlite"
        self.export.write_text(json.dumps(export_fixture()),encoding="utf-8")

    def build(self):
        return build_index(self.export,self.db)

    def test_ten_specialists_and_source_grounded_search(self):
        result=self.build()
        self.assertEqual(result["agents_defined"],10)
        self.assertEqual(len(AGENTS),10)
        self.assertEqual(result["messages_indexed"],5)
        r=recover(self.db,"HANTER")
        self.assertEqual(len(r["agents"]),10)
        self.assertGreaterEqual(r["matches"],1)
        self.assertTrue(all(x["source_ref"].startswith("chatgpt-export:")
                            for x in r["results"]))
        self.assertTrue(all(x["matched_by"] for x in r["results"]))
        self.assertEqual(r["real_nca_workers_executed"],0)
        self.assertEqual(r["llm_calls"],0)
        self.assertFalse(r["remote_chat_access"])

    def test_before_val_town_is_heurstic_and_does_not_invent_start(self):
        self.build()
        r=recover(self.db,"HANTER",before_val_town=True)
        self.assertTrue(r["cutoff_requires_owner_confirmation"])
        self.assertIn("HEURISTIC",r["cutoff_method"])
        self.assertTrue(all(item["created_at_utc"]<"2026-06-02"
                            for item in r["results"]))

    def test_explicit_date_filters_exact_timestamp(self):
        self.build()
        r=recover(self.db,"HANTER",before="2026-05-02")
        self.assertEqual(r["matches"],0)
        r=recover(self.db,"HANTER",before="2026-05-03")
        self.assertGreater(r["matches"],0)
        self.assertEqual(r["cutoff_method"],"OWNER_EXPLICIT_UTC_DATE")

    def test_excludes_alternate_branch_unless_requested(self):
        self.build()
        without=recover(self.db,"superseded")
        self.assertEqual(without["matches"],0)
        with_branches=recover(self.db,"superseded",include_alternates=True)
        self.assertEqual(with_branches["matches"],1)
        self.assertEqual(with_branches["results"][0]["branch_status"],"ALTERNATE")

    def test_secrets_never_indexed_or_returned(self):
        summary=self.build()
        self.assertGreater(summary["messages_with_redactions"],0)
        b=self.db.read_bytes()
        self.assertNotIn(("ghp_"+"A"*40).encode(),b)
        self.assertNotIn(b"john@example.test",b)
        self.assertNotIn(("1234567890:AA"+"B"*40).encode(),b)
        r=recover(self.db,"module")
        data=json.dumps(r)
        self.assertNotIn("ghp_",data)
        self.assertNotIn("john@example.test",data)
        self.assertIn("[REDACTED_CREDENTIAL]",data)

    def test_no_overwrite_private_database(self):
        self.build()
        with self.assertRaisesRegex(RecoveryError,"ALREADY_EXISTS"):
            self.build()

    def test_database_is_owner_read_write_only_on_posix(self):
        self.build()
        self.assertEqual(self.db.stat().st_mode & 0o077,0)

    def test_denies_untrusted_or_absent_chat_input(self):
        with self.assertRaises(RecoveryError):
            build_index(self.root/"no-chat.json",self.db)
        self.export.write_text('{"not":"an array"}',encoding="utf-8")
        with self.assertRaisesRegex(RecoveryError,"EXPECTED_CONVERSATIONS_ARRAY"):
            self.build()
        self.assertFalse(self.db.exists())

    def test_export_symlink_denied(self):
        target=self.root/"elsewhere.json"
        target.write_text("[]")
        self.export.unlink()
        self.export.symlink_to(target)
        with self.assertRaisesRegex(RecoveryError,"SOURCE_NOT_A_REGULAR"):
            self.build()

    def test_database_symlink_denied_for_read(self):
        self.build()
        alias=self.root/"alias.sqlite"
        alias.symlink_to(self.db)
        with self.assertRaisesRegex(RecoveryError,"INDEX_NOT_A_REGULAR"):
            recover(alias,"module")

    def test_rejects_FTS_operator_injection_without_crashing(self):
        self.build()
        r=recover(self.db,'module" OR NEAR(*')
        self.assertEqual(r["schema"],"imperial.plugins.chat-recovery.v1")
        self.assertEqual(r["real_nca_workers_executed"],0)

    def test_invalid_cutoffs_rejected(self):
        self.build()
        for day in ("2026-02-30","0","2026-13-01"):
            with self.subTest(day=day),self.assertRaises(RecoveryError):
                recover(self.db,"HANTER",before=day)
        with self.assertRaises(RecoveryError):
            recover(self.db,"HANTER",before="2026-05-01",before_val_town=True)

    def test_too_many_results_or_empty_query_denied(self):
        self.build()
        for args in ({"query":""},{"query":"test","limit":0},
                     {"query":"test","limit":1000},{"query":"test","limit":True}):
            with self.subTest(args=args),self.assertRaises(RecoveryError):
                recover(self.db,**args)

    def test_redaction_never_replaces_unrelated_code(self):
        self.assertEqual(_redact("HANTER — architecture"),"HANTER — architecture")
        self.assertEqual(_date_limit("2026-05-02"),int(timestamp("2026-05-02")))

    def test_no_valtown_mention_requires_real_owner_cutoff(self):
        self.export.write_text(json.dumps([{
            "id":"chat-only","title":"Core prior notes",
            "current_node":"a", "mapping":{"a":node("a",None,"HANTER documentation", "2026-05-02")}
        }]))
        self.build()
        with self.assertRaisesRegex(RecoveryError,"NO_VAL_TOWN_MENTION"):
            recover(self.db,"HANTER",before_val_town=True)


if __name__=="__main__":
    unittest.main()
