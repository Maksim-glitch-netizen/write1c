#!/usr/bin/env python3
"""Prepare and validate the explicit Type+Name donor merge workflow."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
import xml.etree.ElementTree as ET


MERGE_NS = "http://v8.1c.ru/8.3/config/merge/settings"
ET.register_namespace("", MERGE_NS)

TYPE_DIRECTORIES = {
    "Catalog": "Catalogs",
    "Document": "Documents",
    "Enum": "Enums",
    "Constant": "Constants",
    "InformationRegister": "InformationRegisters",
    "AccumulationRegister": "AccumulationRegisters",
    "AccountingRegister": "AccountingRegisters",
    "CalculationRegister": "CalculationRegisters",
    "ChartOfAccounts": "ChartsOfAccounts",
    "ChartOfCharacteristicTypes": "ChartsOfCharacteristicTypes",
    "ChartOfCalculationTypes": "ChartsOfCalculationTypes",
    "BusinessProcess": "BusinessProcesses",
    "Task": "Tasks",
    "ExchangePlan": "ExchangePlans",
    "DocumentJournal": "DocumentJournals",
    "Report": "Reports",
    "DataProcessor": "DataProcessors",
    "CommonModule": "CommonModules",
    "ScheduledJob": "ScheduledJobs",
    "EventSubscription": "EventSubscriptions",
    "HTTPService": "HTTPServices",
    "WebService": "WebServices",
    "DefinedType": "DefinedTypes",
    "FunctionalOption": "FunctionalOptions",
    "Sequence": "Sequences",
    "FilterCriterion": "FilterCriteria",
    "DocumentNumerator": "DocumentNumerators",
    "SettingsStorage": "SettingsStorages",
    "CommonForm": "CommonForms",
    "SessionParameter": "SessionParameters",
    "CommonCommand": "CommonCommands",
    "CommandGroup": "CommandGroups",
    "CommonAttribute": "CommonAttributes",
    "FunctionalOptionsParameter": "FunctionalOptionsParameters",
    "WSReference": "WSReferences",
    "CommonPicture": "CommonPictures",
    "CommonTemplate": "CommonTemplates",
    "ExternalDataSource": "ExternalDataSources",
}

NAME_RE = re.compile(r"^[A-Za-zА-Яа-яЁё_][A-Za-zА-Яа-яЁё0-9_]*$")


class WorkflowError(RuntimeError):
    pass


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def canonical_type(value: str) -> str:
    for item in TYPE_DIRECTORIES:
        if item.casefold() == value.casefold():
            return item
    raise WorkflowError(
        f"Unsupported metadata type: {value}. Supported: {', '.join(TYPE_DIRECTORIES)}"
    )


def validate_name(value: str) -> str:
    if not NAME_RE.fullmatch(value):
        raise WorkflowError(
            "Object name must start with a letter or underscore and contain only letters, digits, or underscores"
        )
    return value


def configuration_objects(path: Path) -> set[str]:
    if not path.is_file():
        raise WorkflowError(f"Configuration.xml not found: {path}")
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as exc:
        raise WorkflowError(f"Invalid Configuration.xml {path}: {exc}") from exc

    child_nodes = [node for node in root.iter() if local_name(node.tag) == "ChildObjects"]
    if not child_nodes:
        raise WorkflowError(f"ChildObjects not found in {path}")

    result: set[str] = set()
    for child_objects in child_nodes:
        for child in list(child_objects):
            name = (child.text or "").strip()
            if name:
                result.add(f"{local_name(child.tag)}.{name}")
    return result


def read_json(path: Path) -> dict:
    if not path.is_file():
        raise WorkflowError(f"JSON file not found: {path}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise WorkflowError(f"Invalid JSON {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise WorkflowError(f"JSON root must be an object: {path}")
    return value


def write_json(path: Path, value: object) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def merge_tag(name: str) -> str:
    return f"{{{MERGE_NS}}}{name}"


def write_merge_settings(path: Path, target_full_name: str, donor_objects: set[str]) -> None:
    if target_full_name not in donor_objects:
        raise WorkflowError(f"Target object is missing from donor: {target_full_name}")

    root = ET.Element(
        merge_tag("Settings"),
        {"version": "1.1", "platformVersion": "8.3.27"},
    )
    parameters = ET.SubElement(root, merge_tag("Parameters"))
    ET.SubElement(parameters, merge_tag("ConfigurationsRelation")).text = "ConfigurationsNotRelated"
    ET.SubElement(parameters, merge_tag("AllowMainConfigurationObjectDeletion")).text = "false"
    ET.SubElement(parameters, merge_tag("CopyObjectsMode")).text = "false"

    objects_node = ET.SubElement(root, merge_tag("Objects"))
    configuration = ET.SubElement(objects_node, merge_tag("Configuration"))
    ET.SubElement(configuration, merge_tag("MergeRule")).text = "DoNotMerge"

    for full_name in sorted(donor_objects):
        object_node = ET.SubElement(
            objects_node,
            merge_tag("Object"),
            {"fullNameInSecondConfiguration": full_name},
        )
        rule = "GetFromSecondConfiguration" if full_name == target_full_name else "DoNotMerge"
        ET.SubElement(object_node, merge_tag("MergeRule")).text = rule

    ET.indent(root, space="    ")
    ET.ElementTree(root).write(path, encoding="utf-8", xml_declaration=True)


def bootstrap_definition(object_type: str, object_name: str) -> tuple[object, list[str], list[str]]:
    target = {"type": object_type, "name": object_name}
    if object_type != "AccumulationRegister":
        return target, [], []

    full_name = f"{object_type}.{object_name}"
    target["dimensions"] = ["Example_DonorDimension: String(1)"]
    target["resources"] = ["Example_DonorResource: Number(1,0)"]
    suffix = hashlib.sha256(full_name.encode("utf-8")).hexdigest()[:12]
    registrar_name = f"Example_DonorRegistrar_{suffix}"
    registrar = {
        "type": "Document",
        "name": registrar_name,
        "registerRecords": [full_name],
    }
    return (
        [target, registrar],
        [f"Document.{registrar_name}"],
        ["Dimension.Example_DonorDimension", "Resource.Example_DonorResource"],
    )


def load_manifest(path: Path) -> tuple[dict, Path]:
    manifest_path = path.resolve()
    manifest = read_json(manifest_path)
    if manifest.get("schemaVersion") != 1:
        raise WorkflowError("Unsupported manifest schemaVersion")
    baseline_value = manifest.get("baselineConfiguration")
    baseline_hash = manifest.get("baselineSha256")
    if not isinstance(baseline_value, str) or not isinstance(baseline_hash, str):
        raise WorkflowError("Manifest does not contain the protected baseline snapshot")
    baseline_path = Path(baseline_value)
    if not baseline_path.is_file():
        raise WorkflowError(f"Baseline snapshot not found: {baseline_path}")
    actual_hash = hashlib.sha256(baseline_path.read_bytes()).hexdigest()
    if actual_hash != baseline_hash:
        raise WorkflowError(
            f"Baseline snapshot hash mismatch: expected {baseline_hash}, actual {actual_hash}"
        )
    return manifest, manifest_path


def command_prepare(args: argparse.Namespace) -> None:
    object_type = canonical_type(args.type)
    object_name = validate_name(args.name)
    full_name = f"{object_type}.{object_name}"
    baseline = Path(args.baseline_configuration).resolve()
    baseline_objects = configuration_objects(baseline)
    if full_name in baseline_objects:
        raise WorkflowError(f"Object already exists in baseline: {full_name}")

    workspace = Path(args.workspace).resolve()
    if workspace.exists():
        if not workspace.is_dir():
            raise WorkflowError(f"Workspace path is not a directory: {workspace}")
        if any(workspace.iterdir()):
            raise WorkflowError(f"Workspace is not empty: {workspace}")
    else:
        workspace.mkdir(parents=True)

    input_dir = workspace / "input"
    baseline_dir = workspace / "baseline"
    donor_source = workspace / "donor-src"
    donor_database = workspace / "donor-db"
    artifacts = workspace / "artifacts"
    verification = workspace / "verification"
    for directory in (
        input_dir,
        baseline_dir,
        donor_source,
        donor_database,
        artifacts,
        verification,
    ):
        directory.mkdir()

    baseline_snapshot = baseline_dir / "Configuration.xml"
    baseline_bytes = baseline.read_bytes()
    baseline_snapshot.write_bytes(baseline_bytes)

    object_json = input_dir / "object.json"
    object_definition, auxiliary_objects, bootstrap_members = bootstrap_definition(
        object_type, object_name
    )
    write_json(object_json, object_definition)

    manifest = {
        "schemaVersion": 1,
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "platformVersion": "8.3.27",
        "object": {
            "type": object_type,
            "name": object_name,
            "fullName": full_name,
            "directory": TYPE_DIRECTORIES[object_type],
            "bootstrapAuxiliaryObjects": auxiliary_objects,
            "bootstrapMembersToReplace": bootstrap_members,
        },
        "baselineSourceConfiguration": str(baseline),
        "baselineConfiguration": str(baseline_snapshot),
        "baselineSha256": hashlib.sha256(baseline_bytes).hexdigest(),
        "workspace": str(workspace),
        "paths": {
            "objectJson": str(object_json),
            "donorSource": str(donor_source),
            "donorDatabase": str(donor_database),
            "donorCf": str(artifacts / "donor.cf"),
            "mergeSettings": str(artifacts / "MergeSettings.xml"),
            "donorObjects": str(artifacts / "donor-objects.json"),
            "verification": str(verification),
        },
    }
    manifest_path = workspace / "manifest.json"
    write_json(manifest_path, manifest)
    print(f"Prepared: {manifest_path}")
    print(f"Target: {full_name}")


def command_finalize(args: argparse.Namespace) -> None:
    manifest, manifest_path = load_manifest(Path(args.manifest))
    target = manifest["object"]["fullName"]
    donor_source = Path(manifest["paths"]["donorSource"])
    donor_configuration = donor_source / "Configuration.xml"
    donor_objects = configuration_objects(donor_configuration)
    if target not in donor_objects:
        raise WorkflowError(f"Target is not registered in donor Configuration.xml: {target}")
    expected_auxiliary = set(manifest["object"].get("bootstrapAuxiliaryObjects", []))
    missing_auxiliary = expected_auxiliary - donor_objects
    if missing_auxiliary:
        raise WorkflowError(
            f"Bootstrap auxiliary objects are missing from donor: {sorted(missing_auxiliary)}"
        )

    merge_settings = Path(manifest["paths"]["mergeSettings"])
    donor_objects_path = Path(manifest["paths"]["donorObjects"])
    merge_settings.parent.mkdir(parents=True, exist_ok=True)
    write_merge_settings(merge_settings, target, donor_objects)
    write_json(
        donor_objects_path,
        {
            "target": target,
            "objects": [
                {
                    "fullName": item,
                    "mergeRule": (
                        "GetFromSecondConfiguration" if item == target else "DoNotMerge"
                    ),
                }
                for item in sorted(donor_objects)
            ],
        },
    )
    print(f"Finalized: {manifest_path}")
    print(f"Merge settings: {merge_settings}")
    print(f"Donor root objects: {len(donor_objects)}")


def command_verify_main(args: argparse.Namespace) -> None:
    manifest, _ = load_manifest(Path(args.manifest))
    target = manifest["object"]["fullName"]
    baseline_path = Path(manifest["baselineConfiguration"])
    current_source = Path(args.current_source).resolve()
    current_configuration = current_source / "Configuration.xml"

    baseline_objects = configuration_objects(baseline_path)
    current_objects = configuration_objects(current_configuration)
    if target in baseline_objects:
        raise WorkflowError(f"Target unexpectedly exists in baseline: {target}")
    if target not in current_objects:
        raise WorkflowError(f"Target is missing after merge: {target}")

    added = current_objects - baseline_objects
    deleted = baseline_objects - current_objects
    if added != {target}:
        raise WorkflowError(
            f"Unexpected added root objects. Expected [{target}], actual {sorted(added)}"
        )
    if deleted:
        raise WorkflowError(f"Root objects were deleted: {sorted(deleted)}")

    object_info = manifest["object"]
    object_xml = current_source / object_info["directory"] / f"{object_info['name']}.xml"
    if not object_xml.is_file():
        raise WorkflowError(f"Object XML is missing after merge: {object_xml}")
    try:
        ET.parse(object_xml)
    except ET.ParseError as exc:
        raise WorkflowError(f"Object XML is invalid: {object_xml}: {exc}") from exc

    report = {
        "verifiedAt": datetime.now(timezone.utc).isoformat(),
        "target": target,
        "configuration": str(current_configuration),
        "objectXml": str(object_xml),
        "added": sorted(added),
        "deleted": sorted(deleted),
        "result": "success",
    }
    verification_dir = Path(manifest["paths"]["verification"])
    verification_dir.mkdir(parents=True, exist_ok=True)
    report_path = verification_dir / "verify-main.json"
    write_json(report_path, report)
    print(f"Verified: {target}")
    print(f"Report: {report_path}")


def command_verify_ready(args: argparse.Namespace) -> None:
    manifest, _ = load_manifest(Path(args.manifest))
    object_info = manifest["object"]
    target = object_info["fullName"]
    current_source = Path(args.current_source).resolve()
    object_xml = current_source / object_info["directory"] / f"{object_info['name']}.xml"
    if not object_xml.is_file():
        raise WorkflowError(f"Object XML is missing: {object_xml}")
    try:
        object_root = ET.parse(object_xml).getroot()
    except ET.ParseError as exc:
        raise WorkflowError(f"Object XML is invalid: {object_xml}: {exc}") from exc

    bootstrap_names = {
        item.split(".", 1)[1]
        for item in object_info.get("bootstrapMembersToReplace", [])
        if "." in item
    }
    remaining_bootstrap = sorted(
        {
            (node.text or "").strip()
            for node in object_root.iter()
            if local_name(node.tag) == "Name"
            and (node.text or "").strip() in bootstrap_names
        }
    )
    if remaining_bootstrap:
        raise WorkflowError(
            f"Bootstrap members must be replaced before UpdateDBCfg: {remaining_bootstrap}"
        )

    registrars: list[str] = []
    if object_info["type"] == "AccumulationRegister":
        documents_dir = current_source / TYPE_DIRECTORIES["Document"]
        if documents_dir.is_dir():
            for document_xml in sorted(documents_dir.glob("*.xml")):
                try:
                    document_root = ET.parse(document_xml).getroot()
                except ET.ParseError as exc:
                    raise WorkflowError(
                        f"Document XML is invalid while checking registrars: {document_xml}: {exc}"
                    ) from exc
                has_register_record = any(
                    any((item.text or "").strip() == target for item in records.iter())
                    for records in document_root.iter()
                    if local_name(records.tag) == "RegisterRecords"
                )
                if has_register_record:
                    registrars.append(document_xml.stem)
        if not registrars:
            raise WorkflowError(
                f"No real document registrar references {target}; UpdateDBCfg is not allowed"
            )

    report = {
        "verifiedAt": datetime.now(timezone.utc).isoformat(),
        "target": target,
        "objectXml": str(object_xml),
        "remainingBootstrapMembers": remaining_bootstrap,
        "registrars": registrars,
        "result": "success",
    }
    verification_dir = Path(manifest["paths"]["verification"])
    verification_dir.mkdir(parents=True, exist_ok=True)
    report_path = verification_dir / "verify-ready.json"
    write_json(report_path, report)
    print(f"Ready for final validation: {target}")
    print(f"Report: {report_path}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    prepare = subparsers.add_parser("prepare", help="Create a safe workspace and manifest")
    prepare.add_argument("--type", required=True)
    prepare.add_argument("--name", required=True)
    prepare.add_argument("--baseline-configuration", required=True)
    prepare.add_argument("--workspace", required=True)
    prepare.set_defaults(handler=command_prepare)

    finalize = subparsers.add_parser("finalize", help="Validate donor XML and create merge settings")
    finalize.add_argument("--manifest", required=True)
    finalize.set_defaults(handler=command_finalize)

    verify = subparsers.add_parser("verify-main", help="Verify the fresh main XML dump after merge")
    verify.add_argument("--manifest", required=True)
    verify.add_argument("--current-source", required=True)
    verify.set_defaults(handler=command_verify_main)

    ready = subparsers.add_parser(
        "verify-ready", help="Reject donor scaffolding before the final UpdateDBCfg"
    )
    ready.add_argument("--manifest", required=True)
    ready.add_argument("--current-source", required=True)
    ready.set_defaults(handler=command_verify_ready)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        args.handler(args)
    except WorkflowError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
