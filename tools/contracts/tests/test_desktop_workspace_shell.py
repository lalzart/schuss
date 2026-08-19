from __future__ import annotations

from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from packages.schuss_core.control_plane import dispatch_operation, load_repository_context
from packages.schuss_core.workspace_library import WorkspaceLibraryError, WorkspaceLibraryService


def request(operation: str, payload: dict) -> dict:
    return {
        "schema_version": "schuss-operation-request-v15",
        "canonical_profile": "schuss-canonical-json-v1",
        "operation": operation,
        "payload": payload,
    }


class DesktopWorkspaceShellTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.context = load_repository_context(
            ROOT,
            record_set_path=ROOT
            / "contracts/record-sets/ui-desktop-workspace-shell-v1.json",
        )

    def service(self, root: Path) -> WorkspaceLibraryService:
        return WorkspaceLibraryService(
            root,
            repository_root=ROOT,
            initial_context=self.context,
        )

    def test_create_allocates_identity_directory_and_complete_profile(self):
        with tempfile.TemporaryDirectory() as temporary:
            projects_root = Path(temporary) / "projects"
            service = self.service(projects_root)
            first = dispatch_operation(
                request("workspace.project.create", {"display_name": "Noise fold"}),
                self.context,
                workspace_service=service,
            )
            second = dispatch_operation(
                request("workspace.project.create", {"display_name": "Noise fold"}),
                self.context,
                workspace_service=service,
            )
            self.assertEqual("success", first["status"])
            self.assertEqual("success", second["status"])
            self.assertEqual("Noise fold", first["value"]["project"]["display_name"])
            self.assertNotEqual(
                first["value"]["project"]["workspace"],
                second["value"]["project"]["workspace"],
            )
            self.assertNotEqual(
                first["value"]["project"]["project_reference"]["project_id"],
                second["value"]["project"]["project_reference"]["project_id"],
            )
            listed = dispatch_operation(
                request("workspace.projects.list", {}),
                self.context,
                workspace_service=service,
            )
            self.assertEqual(2, listed["value"]["project_count"])
            self.assertEqual(0, listed["value"]["rejected_child_count"])
            self.assertEqual(
                ["Noise fold", "Noise fold"],
                [item["display_name"] for item in listed["value"]["projects"]],
            )

    def test_listing_is_direct_bounded_and_fails_closed_on_symlinks_and_malformed_children(self):
        with tempfile.TemporaryDirectory() as temporary:
            projects_root = Path(temporary) / "projects"
            projects_root.mkdir()
            (projects_root / "malformed").mkdir()
            outside = Path(temporary) / "outside"
            outside.mkdir()
            (projects_root / "linked").symlink_to(outside, target_is_directory=True)
            listed = dispatch_operation(
                request("workspace.projects.list", {}),
                self.context,
                workspace_service=self.service(projects_root),
            )
            self.assertEqual("success", listed["status"])
            self.assertEqual(0, listed["value"]["project_count"])
            self.assertEqual(2, listed["value"]["rejected_child_count"])
            self.assertEqual([], listed["value"]["projects"])

    def test_duplicate_project_identity_excludes_every_duplicate(self):
        with tempfile.TemporaryDirectory() as temporary:
            projects_root = Path(temporary) / "projects"
            service = self.service(projects_root)
            created = dispatch_operation(
                request("workspace.project.create", {"display_name": "Original"}),
                self.context,
                workspace_service=service,
            )
            original = Path(created["value"]["project"]["workspace"])
            shutil.copytree(original, projects_root / "duplicate")
            listed = dispatch_operation(
                request("workspace.projects.list", {}),
                self.context,
                workspace_service=service,
            )
            self.assertEqual(0, listed["value"]["project_count"])
            self.assertEqual(2, listed["value"]["rejected_child_count"])

            original_id = created["value"]["project"]["project_reference"]["project_id"]
            with mock.patch.object(
                service,
                "_allocate_project_id",
                wraps=service._allocate_project_id,
            ) as allocate:
                another = dispatch_operation(
                    request("workspace.project.create", {"display_name": "Another"}),
                    self.context,
                    workspace_service=service,
                )
            self.assertEqual("success", another["status"])
            self.assertIn(original_id, allocate.call_args.args[2])

    def test_creation_fails_closed_when_bounded_root_is_full(self):
        with tempfile.TemporaryDirectory() as temporary:
            projects_root = Path(temporary) / "projects"
            service = WorkspaceLibraryService(
                projects_root,
                repository_root=ROOT,
                initial_context=self.context,
                maximum_projects=1,
            )
            first = dispatch_operation(
                request("workspace.project.create", {"display_name": "First"}),
                self.context,
                workspace_service=service,
            )
            second = dispatch_operation(
                request("workspace.project.create", {"display_name": "Second"}),
                self.context,
                workspace_service=service,
            )
            self.assertEqual("success", first["status"])
            self.assertEqual("conflict", second["status"])
            self.assertEqual(
                "WORKSPACE_PROJECT_LIMIT_REACHED",
                second["diagnostics"][0]["code"],
            )

    def test_root_and_name_negative_cases_return_stable_diagnostics(self):
        with self.assertRaises(WorkspaceLibraryError):
            self.service(Path("relative/projects"))
        with tempfile.TemporaryDirectory() as temporary:
            result = dispatch_operation(
                request("workspace.project.create", {"display_name": "   "}),
                self.context,
                workspace_service=self.service(Path(temporary) / "projects"),
            )
            self.assertEqual("invalid", result["status"])
            self.assertEqual(
                "WORKSPACE_PROJECT_NAME_EMPTY",
                result["diagnostics"][0]["code"],
            )

    def test_application_description_adds_exact_v15_capabilities(self):
        with tempfile.TemporaryDirectory() as temporary:
            result = dispatch_operation(
                {
                    "schema_version": "schuss-operation-request-v7",
                    "canonical_profile": "schuss-canonical-json-v1",
                    "operation": "application.describe",
                    "payload": {"scope": "selected-context"},
                },
                self.context,
                workspace_service=self.service(Path(temporary) / "projects"),
            )
            self.assertEqual("schuss-application-capability-description-v8", result["value"]["description_version"])
            capabilities = {
                item["operation"]: item for item in result["value"]["operations"]
            }
            self.assertEqual(43, len(capabilities))
            self.assertEqual("available", capabilities["workspace.projects.list"]["availability"])
            self.assertEqual("workspace-write", capabilities["workspace.project.create"]["effect_class"])


if __name__ == "__main__":
    unittest.main()
