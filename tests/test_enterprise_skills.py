import unittest
from imperial_plugins.enterprise_skills import EnterpriseSkillsRegistry, validate_enterprise_skill

def example(**changes):
    return {"skill_id":"imperial.skill.code-draft","version":"0.1.0",
            "tenant_id":"tenant-01","orchestrator_id":"engineering-orch",
            "runtime_domain":"CODE_ENGINEERING","capability":"simulate:task",
            "risk_tier":"GUARDED","description":"Non-executing engineering plan proposal",
            "requires_independent_qa":True,"requires_owner_approval":True,
            "external_effects":False,"spend_usd":0,**changes}

class TestEnterpriseSkills(unittest.TestCase):
    def setUp(self):
        self.registry=EnterpriseSkillsRegistry()

    def test_registered_is_not_authority(self):
        r=self.registry.register(example())
        self.assertTrue(r["registered"])
        self.assertFalse(r["execution_authorized"])
        p=self.registry.plan(tenant_id="tenant-01",skill_id="imperial.skill.code-draft",
          orchestrator_id="engineering-orch",runtime_domain="CODE_ENGINEERING",
          capability="simulate:task")
        self.assertTrue(p["planned"])
        self.assertFalse(p["independent_qa_verified"])
        self.assertFalse(p["execution_authorized"])

    def test_immutable_snapshot(self):
        obj=example()
        self.registry.register(obj)
        obj["capability"]="execute:payment"
        snap=self.registry.snapshot()
        snap[0]["risk_tier"]="UNSAFE"
        self.assertEqual(self.registry.snapshot()[0]["capability"],"simulate:task")
        self.assertEqual(self.registry.snapshot()[0]["risk_tier"],"GUARDED")

    def test_duplicate_requires_review(self):
        self.registry.register(example())
        with self.assertRaises(ValueError):self.registry.register(example(version="0.2.0"))

    def test_tenant_orchestrator_domain_capability_isolation(self):
        self.registry.register(example())
        base=dict(tenant_id="tenant-01",skill_id="imperial.skill.code-draft",
          orchestrator_id="engineering-orch",runtime_domain="CODE_ENGINEERING",
          capability="simulate:task")
        for bad in ({"tenant_id":"tenant-02"},{"orchestrator_id":"other-orch"},
                    {"runtime_domain":"SECURITY_DEFENSIVE"},{"capability":"read:public"}):
            with self.subTest(bad=bad):
                self.assertFalse(self.registry.plan(**(base|bad))["planned"])

    def test_external_effect_and_payment_escalation_denied(self):
        for bad in ({"external_effects":True},{"spend_usd":1},{"spend_usd":False},
                    {"requires_owner_approval":False},{"requires_independent_qa":False},
                    {"capability":"execute:payment"},{"risk_tier":"CRITICAL"},
                    {"runtime_domain":"PAYMENTS"},{"version":"01.0.0"}):
            with self.subTest(bad=bad),self.assertRaises(ValueError):
                validate_enterprise_skill(example(**bad))

    def test_unhashable_and_unexpected_fields_are_denied(self):
        for bad in ({"runtime_domain":[]},{"capability":[]},{"risk_tier":[]},
                    {"tenant_id":{}},{"entrypoint":"evil.py"},{"description":None}):
            with self.subTest(bad=bad),self.assertRaises(ValueError):
                validate_enterprise_skill(example(**bad))

    def test_snapshot_is_sorted(self):
        self.registry.register(example(skill_id="imperial.skill.route-check"))
        self.registry.register(example())
        self.assertEqual([x["skill_id"] for x in self.registry.snapshot()],
          ["imperial.skill.code-draft","imperial.skill.route-check"])

if __name__=="__main__":unittest.main()
