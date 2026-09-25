"""Render portable agent prompts and install without overwriting local changes."""
import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HARNESSES = ("claude", "codex", "workbuddy", "codebuddy")


def bundle_path(bundle):
    if not re.fullmatch(r"[a-z][a-z0-9-]*", bundle):
        raise ValueError(f"Invalid bundle name: {bundle}")
    path = (ROOT / bundle).resolve()
    if not path.is_relative_to(ROOT.resolve()) or not (path / "catalog.json").is_file():
        raise ValueError(f"Unknown bundle: {bundle}")
    return path


def bundles():
    return sorted(p.parent.name for p in ROOT.glob("*/catalog.json"))


def catalog(bundle):
    base = bundle_path(bundle)
    data = json.loads((base / "catalog.json").read_text(encoding="utf-8"))
    if data["schema_version"] != 1:
        raise ValueError("Unsupported catalog schema")
    seen = set()
    for agent in data["agents"]:
        name = agent["name"]
        if not re.fullmatch(r"[a-z][a-z0-9-]*", name) or name in seen:
            raise ValueError(f"Invalid or duplicate name: {name}")
        seen.add(name)
        path = (base / agent["prompt"]).resolve()
        if not path.is_relative_to(base / "agents"):
            raise ValueError(f"Prompt outside agents directory: {path}")
        if agent["access"] not in ("read", "write") or not agent["description"].strip():
            raise ValueError(f"Invalid metadata: {name}")
        agent = dict(agent)
        agent["body"] = path.read_text(encoding="utf-8").strip() + "\n"
        if not agent["body"].strip():
            raise ValueError(f"Empty prompt: {name}")
        yield agent


def render(harness, bundle, selected=None):
    if harness not in HARNESSES:
        raise ValueError(f"Unknown harness: {harness}")
    agents = list(catalog(bundle))
    names = {a["name"] for a in agents}
    if selected and set(selected) - names:
        raise ValueError(f"Unknown agents: {sorted(set(selected) - names)}")
    def qualify(text):
        # Keep role references and owner values consistent with installed names.
        for name in sorted(names, key=len, reverse=True):
            text = re.sub(r"(?<![\w-])" + re.escape(name) + r"(?![\w-])", f"{bundle}-{name}", text)
        return text.replace(".sido-agents/workflows/", f".sido-agents/{bundle}/workflows/")

    files = {}
    for a in agents:
        if selected and a["name"] not in selected:
            continue
        a = dict(a, name=f'{bundle}-{a["name"]}', body=qualify(a["body"]), description=qualify(a["description"]))
        quote = lambda s: json.dumps(s, ensure_ascii=False)
        readonly = a["access"] == "read"
        if harness == "codex":
            # JSON strings here are also valid TOML basic strings.
            content = f'name = {quote(a["name"])}\ndescription = {quote(a["description"])}\n'
            if readonly:
                content += 'sandbox_mode = "read-only"\n'
            content += f'developer_instructions = {quote(a["body"])}\n'
            path = f'.codex/agents/{a["name"]}.toml'
        else:
            directory = ".claude" if harness == "claude" else ".codebuddy"
            allowed = "Read, Grep, Glob" + ("" if readonly else ", Edit, Write, Bash")
            content = f'---\nname: {a["name"]}\ndescription: {quote(a["description"])}\ntools: {allowed}\n'
            if readonly:
                content += 'disallowedTools: Write, Edit, Bash\n'
            content += '---\n\n' + a["body"]
            path = f'{directory}/agents/{a["name"]}.md'
        files[path] = content.encode("utf-8")
    workflow_dir = bundle_path(bundle) / "workflows"
    for workflow in sorted(workflow_dir.glob("*.md")):
        files[f".sido-agents/{bundle}/workflows/{workflow.name}"] = qualify(workflow.read_text(encoding="utf-8")).encode("utf-8")
    return files


def write_files(root, files, dry_run=False, generated=False):
    root = root.resolve()
    plan = []
    for relative, content in files.items():
        dest = root / relative
        if not dest.resolve().is_relative_to(root):
            raise ValueError(f"Destination escapes target through a link: {dest}")
        same = dest.is_file() and dest.read_bytes() == content
        if dest.exists() and not same and not generated:
            raise ValueError(f"Existing file differs; no files written. Merge manually: {dest}")
        plan.append((dest, content, same))
    for dest, content, same in plan:
        print(f'{"UNCHANGED" if same else "WOULD WRITE" if dry_run else "WRITE"} {dest}')
        if not dry_run and not same:
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(content)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("list", "build", "install"))
    parser.add_argument("--bundle", help="Named agent bundle; required for build/install")
    parser.add_argument("--harness", choices=(*HARNESSES, "all"), default="all")
    parser.add_argument("--agents", nargs="+", help="Agent names; omitted means all")
    parser.add_argument("--project", type=Path, help="Existing target project (install only)")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    try:
        if args.command == "list":
            for bundle in [args.bundle] if args.bundle else bundles():
                for a in catalog(bundle):
                    print(f'{bundle}/{a["name"]}: {a["description"]}')
            return
        if not args.bundle:
            parser.error("build/install requires --bundle; use list to see available bundles")
        if args.command == "install":
            if args.harness == "all" or not args.project or not args.project.is_dir():
                parser.error("install requires one --harness and an existing --project directory")
            write_files(args.project, render(args.harness, args.bundle, args.agents), args.dry_run)
        else:
            for harness in HARNESSES if args.harness == "all" else (args.harness,):
                write_files(ROOT / "dist" / args.bundle / harness, render(harness, args.bundle, args.agents), args.dry_run, generated=True)
    except (ValueError, OSError, KeyError) as exc:
        parser.exit(1, f"Error: {exc}\n")


if __name__ == "__main__":
    main()
