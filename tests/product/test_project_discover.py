"""Tests for optional Salesforce DX project discovery and component mapping."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from pipelines.product.command_inputs import canonical_project_path  # noqa: E402
from pipelines.product.project_discover import (  # noqa: E402
    discover_salesforce_project,
    map_component_to_local_paths,
)


def write_project(
    root: Path,
    *,
    package_paths: tuple[str, ...] = ("force-app",),
    create_packages: bool = True,
    extra: dict[str, object] | None = None,
) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    payload: dict[str, object] = {
        "packageDirectories": [
            {"path": path, "default": index == 0}
            for index, path in enumerate(package_paths)
        ],
        "namespace": "",
        "sourceApiVersion": "65.0",
    }
    if extra:
        payload.update(extra)
    (root / "sfdx-project.json").write_text(
        json.dumps(payload), encoding="utf-8"
    )
    if create_packages:
        for path in package_paths:
            (root / path).mkdir(parents=True, exist_ok=True)
    return root


class DiscoveryTest(unittest.TestCase):
    def test_explicit_root_wins(self):
        with tempfile.TemporaryDirectory() as temporary:
            project = write_project(Path(temporary) / "project")
            result = discover_salesforce_project(explicit_path=project)
            self.assertEqual(result.status, "found")
            self.assertEqual(result.mode, "explicit")
            self.assertEqual(Path(result.project_root), project.resolve())
            self.assertEqual(result.source_api_version, "65.0")

    def test_explicit_file_inside_project_finds_ancestor(self):
        with tempfile.TemporaryDirectory() as temporary:
            project = write_project(Path(temporary) / "project")
            nested_file = project / "force-app/main/default/classes/A.cls"
            nested_file.parent.mkdir(parents=True)
            nested_file.write_text("public class A {}", encoding="utf-8")
            result = discover_salesforce_project(explicit_path=nested_file)
            self.assertEqual(result.status, "found")
            self.assertEqual(Path(result.project_root), project.resolve())

    def test_invalid_explicit_path_does_not_fall_back(self):
        with tempfile.TemporaryDirectory() as temporary:
            missing = Path(temporary) / "missing"
            result = discover_salesforce_project(explicit_path=missing)
            self.assertEqual(result.status, "invalid")
            self.assertEqual(result.mode, "explicit")

    def test_cwd_inside_project_is_discovered(self):
        with tempfile.TemporaryDirectory() as temporary:
            project = write_project(Path(temporary) / "project")
            nested = project / "force-app/main/default"
            nested.mkdir(parents=True)
            result = discover_salesforce_project(cwd=nested)
            self.assertEqual(result.status, "found")
            self.assertEqual(result.mode, "cwd")

    def test_single_workspace_project_is_discovered(self):
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary) / "workspace"
            project = write_project(workspace / "client/project")
            result = discover_salesforce_project(
                cwd=Path(temporary) / "outside",
                workspace_paths=[workspace],
            )
            self.assertEqual(result.status, "found")
            self.assertEqual(result.mode, "workspace")
            self.assertEqual(Path(result.project_root), project.resolve())

    def test_missing_workspace_warning_does_not_corrupt_found_result(self):
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary) / "workspace"
            project = write_project(workspace / "client/project")
            missing = Path(temporary) / "missing-workspace"
            result = discover_salesforce_project(
                cwd=Path(temporary) / "outside",
                workspace_paths=[missing, workspace],
            )
            self.assertEqual(result.status, "found")
            self.assertEqual(Path(result.project_root), project.resolve())
            self.assertTrue(any(str(missing) in warning for warning in result.warnings))

    def test_multiple_workspace_projects_are_ambiguous(self):
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary) / "workspace"
            first = write_project(workspace / "first")
            second = write_project(workspace / "second")
            result = discover_salesforce_project(
                cwd=Path(temporary) / "outside",
                workspace_paths=[workspace],
            )
            self.assertEqual(result.status, "ambiguous")
            self.assertEqual(
                set(result.candidates), {str(first.resolve()), str(second.resolve())}
            )

    def test_no_project_is_valid_standalone_mode(self):
        with tempfile.TemporaryDirectory() as temporary:
            result = discover_salesforce_project(cwd=temporary)
            self.assertEqual(result.status, "standalone")
            self.assertEqual(result.mode, "standalone")
            self.assertFalse(result.found)

    def test_sfskills_checkout_is_standalone(self):
        result = discover_salesforce_project(cwd=REPO_ROOT)
        self.assertEqual(result.status, "standalone")
        self.assertEqual(result.mode, "standalone")
        self.assertFalse(result.found)

    def test_bundled_empty_dx_fixture_is_not_a_user_project(self):
        fixture = REPO_ROOT / "mcp/sfskills-mcp/resources/empty-sfdx-project"
        result = discover_salesforce_project(explicit_path=fixture)
        self.assertEqual(result.status, "invalid")
        self.assertEqual(result.mode, "explicit")

    def test_workspace_scan_of_sfskills_checkout_is_standalone(self):
        result = discover_salesforce_project(
            cwd=Path("/definitely/not/a/real/path"),
            workspace_paths=[REPO_ROOT],
        )
        self.assertEqual(result.status, "standalone")

    def test_invalid_descriptor_is_reported(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "project"
            root.mkdir()
            (root / "sfdx-project.json").write_text("{bad", encoding="utf-8")
            result = discover_salesforce_project(explicit_path=root)
            self.assertEqual(result.status, "invalid")
            self.assertIn("Invalid JSON", result.warnings[0])

    def test_escaping_package_directory_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            project = write_project(
                Path(temporary) / "project",
                package_paths=("../outside",),
                create_packages=False,
            )
            result = discover_salesforce_project(explicit_path=project)
            self.assertEqual(result.status, "found")
            self.assertEqual(result.package_directories, ())
            self.assertTrue(any("escapes" in warning for warning in result.warnings))


class MappingTest(unittest.TestCase):
    def test_maps_apex_class(self):
        with tempfile.TemporaryDirectory() as temporary:
            project = write_project(Path(temporary) / "project")
            source = project / "force-app/main/default/classes/AccountService.cls"
            source.parent.mkdir(parents=True)
            source.write_text("public class AccountService {}", encoding="utf-8")
            discovery = discover_salesforce_project(explicit_path=project)
            mapping = map_component_to_local_paths(
                discovery,
                component_type="ApexClass",
                full_name="AccountService",
                line=17,
                column=5,
            )
            self.assertEqual(mapping.status, "mapped")
            self.assertEqual(Path(mapping.matches[0].path), source.resolve())
            self.assertEqual(mapping.matches[0].line, 17)

    def test_maps_custom_field(self):
        with tempfile.TemporaryDirectory() as temporary:
            project = write_project(Path(temporary) / "project")
            source = (
                project
                / "force-app/main/default/objects/Account/fields/Customer_Tier__c.field-meta.xml"
            )
            source.parent.mkdir(parents=True)
            source.write_text("<CustomField/>", encoding="utf-8")
            discovery = discover_salesforce_project(explicit_path=project)
            mapping = map_component_to_local_paths(
                discovery,
                component_type="CustomField",
                full_name="Account.Customer_Tier__c",
            )
            self.assertEqual(mapping.status, "mapped")
            self.assertEqual(Path(mapping.matches[0].path), source.resolve())

    def test_maps_lwc_bundle_directory(self):
        with tempfile.TemporaryDirectory() as temporary:
            project = write_project(Path(temporary) / "project")
            bundle = project / "force-app/main/default/lwc/accountPanel"
            bundle.mkdir(parents=True)
            (bundle / "accountPanel.js").write_text("export default class {}", encoding="utf-8")
            discovery = discover_salesforce_project(explicit_path=project)
            mapping = map_component_to_local_paths(
                discovery,
                component_type="LightningComponentBundle",
                full_name="accountPanel",
            )
            self.assertEqual(mapping.status, "mapped")
            self.assertEqual(Path(mapping.matches[0].path), bundle.resolve())

    def test_not_found_is_honest(self):
        with tempfile.TemporaryDirectory() as temporary:
            project = write_project(Path(temporary) / "project")
            discovery = discover_salesforce_project(explicit_path=project)
            mapping = map_component_to_local_paths(
                discovery,
                component_type="ApexClass",
                full_name="MissingClass",
            )
            self.assertEqual(mapping.status, "not_found")
            self.assertEqual(mapping.matches, ())

    def test_standalone_mapping_is_skipped_not_failed(self):
        discovery = discover_salesforce_project(cwd="/definitely/not/a/real/path")
        mapping = map_component_to_local_paths(
            discovery,
            component_type="ApexClass",
            full_name="AccountService",
        )
        self.assertIn(mapping.status, {"standalone", "project_unavailable"})
        self.assertEqual(mapping.matches, ())

    def test_unsafe_full_name_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            project = write_project(Path(temporary) / "project")
            discovery = discover_salesforce_project(explicit_path=project)
            mapping = map_component_to_local_paths(
                discovery,
                component_type="ApexClass",
                full_name="../../secret",
            )
            self.assertEqual(mapping.status, "invalid_component")

    def test_non_positive_line_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            project = write_project(Path(temporary) / "project")
            discovery = discover_salesforce_project(explicit_path=project)
            mapping = map_component_to_local_paths(
                discovery,
                component_type="ApexClass",
                full_name="AccountService",
                line=0,
            )
            self.assertEqual(mapping.status, "invalid_component")


class CliTest(unittest.TestCase):
    def test_cli_json_standalone_exits_zero_by_default(self):
        script = REPO_ROOT / "scripts/sf_project_inspector.py"
        with tempfile.TemporaryDirectory() as temporary:
            completed = subprocess.run(
                [sys.executable, str(script), "--cwd", temporary, "--json"],
                cwd=REPO_ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["discovery"]["status"], "standalone")

    def test_cli_requires_component_pair(self):
        script = REPO_ROOT / "scripts/sf_project_inspector.py"
        completed = subprocess.run(
            [sys.executable, str(script), "--component-type", "ApexClass"],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 2)
        self.assertIn("must be supplied together", completed.stderr)

    def test_cli_repo_path_alias_maps_explicit_project(self):
        script = REPO_ROOT / "scripts/sf_project_inspector.py"
        with tempfile.TemporaryDirectory() as temporary:
            project = write_project(Path(temporary) / "project")
            completed = subprocess.run(
                [
                    sys.executable,
                    str(script),
                    "--repo-path",
                    str(project),
                    "--json",
                ],
                cwd=REPO_ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["discovery"]["status"], "found")
        self.assertEqual(payload["discovery"]["mode"], "explicit")


class ProductWiringTest(unittest.TestCase):
    def test_plugin_packages_inspector_once(self):
        agents_dir = REPO_ROOT / "integrations/cursor/agents"
        names = [path.name for path in agents_dir.glob("*.md")]
        self.assertEqual(names.count("sf-project-inspector.md"), 1)
        self.assertNotIn("sf-repo-mapper.md", names)
        self.assertEqual(len(names), 5)

    def test_triage_continues_when_local_mapping_unavailable(self):
        paths = (
            REPO_ROOT / "integrations/cursor/commands/triage-deployment.md",
            REPO_ROOT / "commands/triage-deployment.md",
        )
        for path in paths:
            text = path.read_text(encoding="utf-8")
            self.assertNotIn("sf-repo-mapper", text)
            self.assertIn("standalone", text)
            self.assertIn("project_path", text)

    def test_project_path_aliases(self):
        self.assertEqual(
            canonical_project_path({"repo_path": "/work/app", "source_path": "/ignored"}),
            "/work/app",
        )
        self.assertEqual(
            canonical_project_path({"project_path": "/canonical"}),
            "/canonical",
        )
        self.assertIsNone(canonical_project_path({}))


if __name__ == "__main__":
    unittest.main()
