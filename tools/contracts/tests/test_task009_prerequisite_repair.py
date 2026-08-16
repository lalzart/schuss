import hashlib
import json
import unittest
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
EVIDENCE = ROOT / "evidence/task-009-prerequisite-repair-v1"
STORE = ROOT / "build/task009-prerequisite-repair-v1/content-addressed"


def load(name):
    return json.loads((EVIDENCE / name).read_text(encoding="utf-8"))


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class Task009PrerequisiteRepairTest(unittest.TestCase):
    def test_repair_evidence_manifest_is_exact(self):
        manifest = load("repair-evidence-manifest.json")
        self.assertEqual(12, manifest["member_count"])
        for member in manifest["members"]:
            path = ROOT / member["portable_path"]
            self.assertEqual(member["byte_length"], path.stat().st_size)
            self.assertEqual(member["byte_sha256"], sha256(path))

    def test_accepted_input_preservation_is_current(self):
        preservation = load("pre-repair-preservation.json")
        self.assertGreater(preservation["member_count"], 30)
        for member in preservation["members"]:
            path = ROOT / member["portable_path"]
            self.assertEqual(member["byte_length"], path.stat().st_size)
            self.assertEqual(member["byte_sha256"], sha256(path))
        post = load("post-repair-preservation.json")
        self.assertEqual("passed", post["status"])
        self.assertEqual(
            preservation["root_fingerprint_sha256"],
            post["before_fingerprint_sha256"],
        )

    def test_expanded_arm_vectors_are_commands_not_progress_text(self):
        document = load("firmware-expanded-command-vectors.json")
        self.assertEqual(194, document["command_count"])
        self.assertEqual(list(range(194)), [item["index"] for item in document["commands"]])
        self.assertTrue(all(item["exit_status"] == 0 for item in document["commands"]))
        roles = Counter(item["role"] for item in document["commands"])
        self.assertEqual(182, roles["compiler-driver"])
        self.assertEqual(3, roles["assembler-driver"])
        self.assertEqual(1, roles["linker-driver"])
        linker = next(item for item in document["commands"] if item["role"] == "linker-driver")
        self.assertIn("-mfloat-abi=hard", linker["arguments"])
        self.assertIn("-mfpu=fpv4-sp-d16", linker["arguments"])
        self.assertTrue(any("--script=STM32F427xG_ksoloti.ld" in item for item in linker["arguments"]))
        self.assertEqual(185, sum(item.endswith(".o") for item in linker["arguments"]))
        text = (EVIDENCE / "firmware-expanded-command-vectors.json").read_text(encoding="utf-8")
        for forbidden in ("/Users/", "/private", "/tmp/", "/Applications/", "/opt/homebrew/"):
            self.assertNotIn(forbidden, text)
        self.assertTrue(
            all(item["working_directory"] == "source-capsule/firmware" for item in document["commands"])
        )
        self.assertEqual("system-tools/bin/make", document["build_invocation"]["arguments"][0])
        self.assertNotIn("Compiling", text)
        self.assertNotIn("Memory region", text)

    def test_compiled_classes_match_the_accepted_member_oracle(self):
        repaired = load("java-class-members.json")
        accepted = json.loads(
            (ROOT / "evidence/task-009-prerequisite-v0/java-classpath-members.json").read_text(encoding="utf-8")
        )
        accepted_classes = [
            {key: member[key] for key in ("byte_length", "byte_sha256", "path")}
            for member in accepted["members"]
            if member["kind"] == "class"
        ]
        self.assertEqual(896, repaired["class_count"])
        self.assertEqual(accepted_classes, repaired["members"])
        self.assertEqual(
            "5ebd2f2b7f2aa6dc1d3d10a04edb5f2bbedd97cfb4372dab56dc22c778b17710",
            repaired["classpath_fingerprint_sha256"],
        )

    def test_ant_closure_has_no_ambient_or_user_library_authority(self):
        document = load("java-ant-executable-closure.json")
        self.assertEqual("disabled", document["ambient_classpath"])
        self.assertEqual("disabled", document["user_libraries"])
        self.assertEqual(57, document["ant_home_library_member_count"])
        paths = {item["path"] for item in document["ant_home_library_members"]}
        self.assertIn("ant-home/lib/ant-launcher.jar", paths)
        self.assertIn("ant-home/lib/ant.jar", paths)
        command = document["java_build_command"]
        self.assertIn("org.apache.tools.ant.launch.Launcher", command["arguments"])
        self.assertIn("-nouserlib", command["arguments"])
        self.assertIn("-lib", command["arguments"])
        self.assertIn("CLASSPATH=", command["environment"])
        self.assertIn("PATH=system-tools/bin", command["environment"])

    @unittest.skipUnless(
        STORE.is_dir(),
        "authenticated local Task 009 content store is unavailable; validate it separately when present",
    )
    def test_retained_content_addresses_are_present_and_exact(self):
        document = load("retained-products.json")
        self.assertEqual(6, len(document["products"]))
        kinds = {item["kind"] for item in document["products"]}
        self.assertIn("compiled-java-class-tar", kinds)
        self.assertIn("canonical-stripped-firmware-link-elf", kinds)
        self.assertIn("canonical-firmware-bin", kinds)
        for product in document["products"]:
            path = STORE / product["portable_locator"]
            self.assertTrue(path.is_file())
            self.assertEqual(product["byte_length"], path.stat().st_size)
            self.assertEqual(product["byte_sha256"], sha256(path))

    def test_real_generation_probe_is_isolated_and_exact(self):
        probe = load("explicit-legacy-isolation-probe.json")
        self.assertEqual("passed", probe["status"])
        self.assertTrue(probe["memory_only_preferences_preserved"])
        self.assertTrue(probe["factory_tree_unchanged"])
        self.assertEqual("generatedobjects.Mixer", probe["generator_class"])
        self.assertEqual("objects/mix/xfade.axo", probe["output_path"])
        self.assertEqual(
            [["i1", "frac32buffer"], ["i2", "frac32buffer"], ["c", "frac32.positive"]],
            probe["inlets"],
        )
        self.assertEqual([["o", "frac32buffer"]], probe["outlets"])
        report = load("legacy-isolation-report.json")
        self.assertEqual(0, report["direct_bytecode_forbidden_references"])
        self.assertEqual(0, report["user_preference_work_files_written"])
        self.assertTrue(all(report["negative_controls"].values()))

    def test_both_clean_roots_match_and_all_stop_codes_close(self):
        equality = load("reproduction-equality.json")
        self.assertEqual("passed", equality["status"])
        self.assertTrue(all(equality["comparisons"].values()))
        verdicts = load("stop-code-verdicts.json")
        self.assertEqual("ready-for-task009-preflight-restart", verdicts["restart_verdict"])
        self.assertEqual(5, len(verdicts["stop_codes"]))
        self.assertTrue(all(item["status"] == "closed" for item in verdicts["stop_codes"]))


if __name__ == "__main__":
    unittest.main()
