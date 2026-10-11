from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import xml.etree.ElementTree as ET


SCRIPT = Path(__file__).parents[1] / "scripts" / "new_object_workflow.py"
SPEC = importlib.util.spec_from_file_location("new_object_workflow", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def write_configuration(path: Path, objects: list[tuple[str, str]]) -> None:
    root = ET.Element("MetaDataObject")
    configuration = ET.SubElement(root, "Configuration")
    children = ET.SubElement(configuration, "ChildObjects")
    for object_type, name in objects:
        ET.SubElement(children, object_type).text = name
    ET.ElementTree(root).write(path, encoding="utf-8", xml_declaration=True)


def write_object(path: Path, names: list[str]) -> None:
    root = ET.Element("MetaDataObject")
    child_objects = ET.SubElement(root, "ChildObjects")
    for name in names:
        child = ET.SubElement(child_objects, "Dimension")
        properties = ET.SubElement(child, "Properties")
        ET.SubElement(properties, "Name").text = name
    ET.ElementTree(root).write(path, encoding="utf-8", xml_declaration=True)


def write_document_registrar(path: Path, target: str) -> None:
    root = ET.Element("MetaDataObject")
    properties = ET.SubElement(root, "Properties")
    records = ET.SubElement(properties, "RegisterRecords")
    ET.SubElement(records, "Item").text = target
    ET.ElementTree(root).write(path, encoding="utf-8", xml_declaration=True)


class WorkflowTests(unittest.TestCase):
    def test_prepare_accumulation_register_adds_donor_only_registrar(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            baseline = root / "Configuration.xml"
            write_configuration(baseline, [("Language", "Русский")])
            workspace = root / "workspace"
            args = type(
                "Args",
                (),
                {
                    "type": "AccumulationRegister",
                    "name": "Example_Test",
                    "baseline_configuration": str(baseline),
                    "workspace": str(workspace),
                },
            )()
            MODULE.command_prepare(args)
            definition = json.loads((workspace / "input" / "object.json").read_text(encoding="utf-8"))
            self.assertIsInstance(definition, list)
            self.assertEqual(definition[0]["type"], "AccumulationRegister")
            self.assertEqual(definition[0]["name"], "Example_Test")
            self.assertEqual(definition[0]["dimensions"], ["Example_DonorDimension: String(1)"])
            self.assertEqual(definition[0]["resources"], ["Example_DonorResource: Number(1,0)"])
            self.assertEqual(definition[1]["type"], "Document")
            self.assertEqual(
                definition[1]["registerRecords"],
                ["AccumulationRegister.Example_Test"],
            )
            manifest = json.loads((workspace / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(
                Path(manifest["baselineConfiguration"]),
                workspace / "baseline" / "Configuration.xml",
            )
            self.assertTrue((workspace / "baseline" / "Configuration.xml").is_file())
            self.assertEqual(
                manifest["object"]["bootstrapMembersToReplace"],
                ["Dimension.Example_DonorDimension", "Resource.Example_DonorResource"],
            )

    def test_prepare_rejects_existing_object(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            baseline = root / "Configuration.xml"
            write_configuration(baseline, [("AccumulationRegister", "Example_Test")])
            args = type(
                "Args",
                (),
                {
                    "type": "AccumulationRegister",
                    "name": "Example_Test",
                    "baseline_configuration": str(baseline),
                    "workspace": str(root / "workspace"),
                },
            )()
            with self.assertRaises(MODULE.WorkflowError):
                MODULE.command_prepare(args)

    def test_finalize_explicitly_blocks_auxiliary_objects(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            baseline = root / "baseline.xml"
            write_configuration(baseline, [("Language", "Русский")])
            workspace = root / "workspace"
            prepare_args = type(
                "Args",
                (),
                {
                    "type": "AccumulationRegister",
                    "name": "Example_Test",
                    "baseline_configuration": str(baseline),
                    "workspace": str(workspace),
                },
            )()
            MODULE.command_prepare(prepare_args)
            manifest = json.loads((workspace / "manifest.json").read_text(encoding="utf-8"))
            auxiliary = manifest["object"]["bootstrapAuxiliaryObjects"][0]
            auxiliary_type, auxiliary_name = auxiliary.split(".", 1)
            write_configuration(
                workspace / "donor-src" / "Configuration.xml",
                [
                    ("Language", "Русский"),
                    ("AccumulationRegister", "Example_Test"),
                    (auxiliary_type, auxiliary_name),
                ],
            )
            finalize_args = type("Args", (), {"manifest": str(workspace / "manifest.json")})()
            MODULE.command_finalize(finalize_args)

            namespace = {"m": MODULE.MERGE_NS}
            settings = ET.parse(workspace / "artifacts" / "MergeSettings.xml")
            rules = {}
            for node in settings.findall(".//m:Object", namespace):
                rules[node.attrib["fullNameInSecondConfiguration"]] = node.findtext(
                    "m:MergeRule", namespaces=namespace
                )
            self.assertEqual(rules["AccumulationRegister.Example_Test"], "GetFromSecondConfiguration")
            self.assertEqual(rules["Language.Русский"], "DoNotMerge")
            self.assertEqual(rules[auxiliary], "DoNotMerge")

    def test_verify_main_requires_only_target_addition(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            baseline = root / "baseline.xml"
            write_configuration(baseline, [("Language", "Русский")])
            workspace = root / "workspace"
            prepare_args = type(
                "Args",
                (),
                {
                    "type": "AccumulationRegister",
                    "name": "Example_Test",
                    "baseline_configuration": str(baseline),
                    "workspace": str(workspace),
                },
            )()
            MODULE.command_prepare(prepare_args)

            # Имитируем реальную повторную выгрузку в тот же каталог: исходный файл baseline
            # изменился, но verify-main обязан использовать снимок внутри workspace.
            write_configuration(
                baseline,
                [("Language", "Русский"), ("AccumulationRegister", "Example_Test")],
            )

            current = root / "current"
            (current / "AccumulationRegisters").mkdir(parents=True)
            write_configuration(
                current / "Configuration.xml",
                [("Language", "Русский"), ("AccumulationRegister", "Example_Test")],
            )
            ET.ElementTree(ET.Element("MetaDataObject")).write(
                current / "AccumulationRegisters" / "Example_Test.xml",
                encoding="utf-8",
                xml_declaration=True,
            )
            verify_args = type(
                "Args",
                (),
                {
                    "manifest": str(workspace / "manifest.json"),
                    "current_source": str(current),
                },
            )()
            MODULE.command_verify_main(verify_args)
            report = json.loads(
                (workspace / "verification" / "verify-main.json").read_text(encoding="utf-8")
            )
            self.assertEqual(report["result"], "success")
            self.assertEqual(report["added"], ["AccumulationRegister.Example_Test"])

    def test_verify_rejects_modified_baseline_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            baseline = root / "baseline.xml"
            write_configuration(baseline, [("Language", "Русский")])
            workspace = root / "workspace"
            prepare_args = type(
                "Args",
                (),
                {
                    "type": "Report",
                    "name": "Example_TestReport",
                    "baseline_configuration": str(baseline),
                    "workspace": str(workspace),
                },
            )()
            MODULE.command_prepare(prepare_args)
            (workspace / "baseline" / "Configuration.xml").write_text(
                "modified", encoding="utf-8"
            )
            verify_args = type(
                "Args",
                (),
                {
                    "manifest": str(workspace / "manifest.json"),
                    "current_source": str(root / "current"),
                },
            )()
            with self.assertRaisesRegex(MODULE.WorkflowError, "hash mismatch"):
                MODULE.command_verify_main(verify_args)

    def test_verify_ready_requires_replacing_scaffold_and_real_registrar(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            baseline = root / "baseline.xml"
            write_configuration(baseline, [("Language", "Русский")])
            workspace = root / "workspace"
            prepare_args = type(
                "Args",
                (),
                {
                    "type": "AccumulationRegister",
                    "name": "Example_Test",
                    "baseline_configuration": str(baseline),
                    "workspace": str(workspace),
                },
            )()
            MODULE.command_prepare(prepare_args)

            current = root / "current"
            registers = current / "AccumulationRegisters"
            documents = current / "Documents"
            registers.mkdir(parents=True)
            documents.mkdir()
            object_path = registers / "Example_Test.xml"
            write_object(object_path, ["Example_DonorDimension"])
            ready_args = type(
                "Args",
                (),
                {
                    "manifest": str(workspace / "manifest.json"),
                    "current_source": str(current),
                },
            )()
            with self.assertRaisesRegex(MODULE.WorkflowError, "Bootstrap members"):
                MODULE.command_verify_ready(ready_args)

            write_object(object_path, ["Компания", "Сумма"])
            with self.assertRaisesRegex(MODULE.WorkflowError, "No real document registrar"):
                MODULE.command_verify_ready(ready_args)

            write_document_registrar(
                documents / "РеальныйДокумент.xml",
                "AccumulationRegister.Example_Test",
            )
            MODULE.command_verify_ready(ready_args)
            report = json.loads(
                (workspace / "verification" / "verify-ready.json").read_text(encoding="utf-8")
            )
            self.assertEqual(report["registrars"], ["РеальныйДокумент"])


if __name__ == "__main__":
    unittest.main()
