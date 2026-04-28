#!/usr/bin/env python3
"""Generate Docusaurus MDX API reference for tethysext.atcore.

This script walks the ``tethysext/atcore/`` package using only Python's
standard ``ast`` module — it never imports the project. That keeps the
docs build hermetic: it doesn't need GDAL, Tethys, Django, or any of
the other heavy runtime dependencies installed.

Output goes under ``website/docs/api/`` mirroring the package layout.
The script is idempotent: rerunning it produces byte-identical output.

Ordering:
- Modules and subpackages: alphabetical.
- Classes and top-level functions: source order (preserves intended
  reading order from the author).
- Methods within a class: source order.
"""

from __future__ import annotations

import ast
import json
import os
import re
import shutil
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

# Repo paths -----------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parents[2]
PACKAGE_ROOT = REPO_ROOT / "tethysext" / "atcore"
API_DOCS_ROOT = REPO_ROOT / "website" / "docs" / "api"
PACKAGE_DOTTED = "tethysext.atcore"

# Subpackages and top-level modules to include. Names match entries
# directly under ``tethysext/atcore/``. Anything not listed here is
# skipped — this keeps non-Python asset directories (templates, sql,
# job scripts, public, tests) out of the API reference.
TOP_LEVEL_TARGETS: set[str] = {
    "cli",
    "controllers",
    "exceptions",
    "forms",
    "gizmos",
    "handlers.py",
    "mixins",
    "models",
    "permissions",
    "services",
    "urls",
    "utilities.py",
}

# Subpackage display labels (alphabetic position is 1..N below).
SUBPACKAGE_LABELS = {
    "cli": "cli",
    "controllers": "controllers",
    "exceptions": "exceptions",
    "forms": "forms",
    "gizmos": "gizmos",
    "handlers": "handlers",
    "mixins": "mixins",
    "models": "models",
    "permissions": "permissions",
    "resources": "resources",
    "services": "services",
    "urls": "urls",
    "utilities": "utilities",
}


# ---------------------------------------------------------------------------
# AST extraction
# ---------------------------------------------------------------------------


@dataclass
class FunctionInfo:
    name: str
    signature: str
    docstring: str | None
    decorators: list[str]
    is_async: bool


@dataclass
class ClassInfo:
    name: str
    bases: list[str]
    docstring: str | None
    decorators: list[str]
    methods: list[FunctionInfo] = field(default_factory=list)


@dataclass
class ModuleInfo:
    dotted_name: str  # e.g. tethysext.atcore.services.foo
    rel_path: Path  # path under PACKAGE_ROOT, e.g. services/foo.py
    docstring: str | None
    classes: list[ClassInfo] = field(default_factory=list)
    functions: list[FunctionInfo] = field(default_factory=list)


def _unparse(node: ast.AST | None) -> str:
    if node is None:
        return ""
    try:
        return ast.unparse(node)
    except Exception:
        return "<unparseable>"


def _format_arguments(args: ast.arguments) -> str:
    parts: list[str] = []

    # positional-only
    posonly = list(args.posonlyargs)
    regular = list(args.args)
    defaults = list(args.defaults)

    total_positional = posonly + regular
    # defaults align to the tail of total_positional
    n_defaults = len(defaults)
    n_positional = len(total_positional)
    default_offset = n_positional - n_defaults

    for idx, arg in enumerate(total_positional):
        piece = arg.arg
        if arg.annotation is not None:
            piece += f": {_unparse(arg.annotation)}"
        if idx >= default_offset:
            default_node = defaults[idx - default_offset]
            piece += f"={_unparse(default_node)}"
        parts.append(piece)
        if posonly and idx == len(posonly) - 1:
            parts.append("/")

    if args.vararg is not None:
        v = "*" + args.vararg.arg
        if args.vararg.annotation is not None:
            v += f": {_unparse(args.vararg.annotation)}"
        parts.append(v)
    elif args.kwonlyargs:
        parts.append("*")

    for kw, default in zip(args.kwonlyargs, args.kw_defaults):
        piece = kw.arg
        if kw.annotation is not None:
            piece += f": {_unparse(kw.annotation)}"
        if default is not None:
            piece += f"={_unparse(default)}"
        parts.append(piece)

    if args.kwarg is not None:
        k = "**" + args.kwarg.arg
        if args.kwarg.annotation is not None:
            k += f": {_unparse(args.kwarg.annotation)}"
        parts.append(k)

    return ", ".join(parts)


def _function_signature(node: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
    args = _format_arguments(node.args)
    sig = f"{node.name}({args})"
    if node.returns is not None:
        sig += f" -> {_unparse(node.returns)}"
    return sig


def _decorator_list(node: ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef) -> list[str]:
    return [_unparse(d) for d in node.decorator_list]


def _is_public(name: str) -> bool:
    # Dunder methods (e.g. __init__) are documented; single-underscore are private.
    if name.startswith("__") and name.endswith("__"):
        return True
    return not name.startswith("_")


def _extract_function(node: ast.FunctionDef | ast.AsyncFunctionDef) -> FunctionInfo:
    return FunctionInfo(
        name=node.name,
        signature=_function_signature(node),
        docstring=ast.get_docstring(node, clean=True),
        decorators=_decorator_list(node),
        is_async=isinstance(node, ast.AsyncFunctionDef),
    )


def _extract_class(node: ast.ClassDef) -> ClassInfo:
    bases = [_unparse(b) for b in node.bases]
    methods: list[FunctionInfo] = []
    for child in node.body:
        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if not _is_public(child.name):
                continue
            methods.append(_extract_function(child))
    return ClassInfo(
        name=node.name,
        bases=bases,
        docstring=ast.get_docstring(node, clean=True),
        decorators=_decorator_list(node),
        methods=methods,
    )


def parse_module(path: Path, dotted_name: str) -> ModuleInfo | None:
    try:
        source = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError) as exc:
        print(f"Skipping {path}: {exc}", file=sys.stderr)
        return None

    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError as exc:
        print(f"Syntax error in {path}: {exc}", file=sys.stderr)
        return None

    module = ModuleInfo(
        dotted_name=dotted_name,
        rel_path=path.relative_to(PACKAGE_ROOT),
        docstring=ast.get_docstring(tree, clean=True),
    )

    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            if not _is_public(node.name):
                continue
            module.classes.append(_extract_class(node))
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if not _is_public(node.name):
                continue
            module.functions.append(_extract_function(node))

    return module


# ---------------------------------------------------------------------------
# Filesystem walking
# ---------------------------------------------------------------------------


def is_skipped_dir(name: str) -> bool:
    return name in {"__pycache__", "tests"} or name.endswith(".egg-info")


def is_module_file(path: Path) -> bool:
    if path.suffix != ".py":
        return False
    stem = path.stem
    if stem == "__init__":
        return True
    if stem.startswith("_"):
        return False
    return True


def iter_modules(start: Path, dotted_prefix: str) -> Iterable[tuple[Path, str]]:
    """Yield (path, dotted_name) for every .py module to document."""
    for entry in sorted(start.iterdir(), key=lambda p: p.name):
        if entry.is_dir():
            if is_skipped_dir(entry.name) or entry.name.startswith("."):
                continue
            if entry.name.startswith("_") and entry.name != "__init__.py":
                continue
            sub_init = entry / "__init__.py"
            if not sub_init.exists():
                # not a package
                continue
            yield from iter_modules(entry, f"{dotted_prefix}.{entry.name}")
        elif entry.is_file():
            if not is_module_file(entry):
                continue
            if entry.name == "__init__.py":
                yield entry, dotted_prefix
            else:
                yield entry, f"{dotted_prefix}.{entry.stem}"


# ---------------------------------------------------------------------------
# MDX rendering
# ---------------------------------------------------------------------------


SLUG_RE = re.compile(r"[^a-z0-9]+")


def slugify(*parts: str) -> str:
    joined = "-".join(parts)
    joined = joined.lower()
    joined = SLUG_RE.sub("-", joined).strip("-")
    return joined or "section"


def escape_mdx_text(text: str) -> str:
    """Make a docstring safe for MDX without altering meaning.

    Strategy: render the docstring as a fenced code block. This is
    robust against ``<``, ``>``, ``{``, ``}``, backslashes, and nested
    Markdown that would otherwise confuse MDX. We only need to ensure
    the fence itself isn't shadowed by a longer fence inside the text.
    """
    # Escape literal triple-backticks by switching the fence to a longer one.
    fence = "```"
    while fence in text:
        fence += "`"
    return f"{fence}text\n{text}\n{fence}\n"


def escape_inline_code(text: str) -> str:
    """Wrap a piece of code (signature, base list, decorator) in inline backticks.

    If the text itself contains backticks, escape with extra backticks.
    """
    if "`" not in text:
        return f"`{text}`"
    # Use double backticks if single backticks appear inside.
    return f"`` {text} ``"


def heading_id(*parts: str) -> str:
    return slugify(*parts)


def _render_decorators(decorators: list[str]) -> str:
    if not decorators:
        return ""
    pieces = []
    for d in decorators:
        pieces.append(f"`@{d}`")
    return "*" + " ".join(pieces) + "*\n\n"


def _render_function(func: FunctionInfo, anchor: str, level: int = 4) -> list[str]:
    out: list[str] = []
    hashes = "#" * level
    out.append(_render_decorators(func.decorators).rstrip("\n"))
    if out and out[-1]:
        out.append("")
    prefix = "async " if func.is_async else ""
    sig_text = f"{prefix}{func.signature}"
    out.append(f"{hashes} {escape_inline_code(sig_text)} \\{{#{anchor}\\}}")
    out.append("")
    if func.docstring:
        out.append(escape_mdx_text(func.docstring))
    else:
        out.append("> _No description._")
        out.append("")
    return out


def _render_class(cls: ClassInfo, module_dotted: str) -> list[str]:
    out: list[str] = []
    class_anchor = heading_id(cls.name)
    bases_text = f"({', '.join(cls.bases)})" if cls.bases else ""
    header = f"### {escape_inline_code(cls.name + bases_text)} \\{{#{class_anchor}\\}}"
    out.append(_render_decorators(cls.decorators).rstrip("\n"))
    if out and out[-1]:
        out.append("")
    out.append(header)
    out.append("")
    if cls.docstring:
        out.append(escape_mdx_text(cls.docstring))
    else:
        out.append("> _No description._")
        out.append("")

    if cls.methods:
        out.append("#### Methods")
        out.append("")
        for method in cls.methods:
            method_anchor = heading_id(cls.name, method.name)
            out.extend(_render_function(method, method_anchor, level=5))
            out.append("")
    return out


def render_module(module: ModuleInfo) -> str:
    # Determine doc id: drop the package prefix, use dot-joined.
    short = module.dotted_name[len(PACKAGE_DOTTED) + 1:] if module.dotted_name != PACKAGE_DOTTED else "index"
    sidebar_label = short.split(".")[-1] if short != "index" else "Overview"

    lines: list[str] = []
    lines.append("---")
    lines.append(f"id: {short}")
    lines.append(f"title: {module.dotted_name}")
    lines.append(f"sidebar_label: {sidebar_label}")
    lines.append("---")
    lines.append("")
    lines.append(f"# `{module.dotted_name}`")
    lines.append("")
    if module.docstring:
        lines.append(escape_mdx_text(module.docstring))
    else:
        lines.append("> _No description._")
        lines.append("")

    if module.classes:
        lines.append("## Classes")
        lines.append("")
        for cls in module.classes:
            lines.extend(_render_class(cls, module.dotted_name))
            lines.append("")

    if module.functions:
        lines.append("## Functions")
        lines.append("")
        for func in module.functions:
            anchor = heading_id(func.name)
            lines.extend(_render_function(func, anchor, level=3))
            lines.append("")

    if not module.classes and not module.functions:
        lines.append("_This module exposes no public classes or functions._")
        lines.append("")

    # Normalize trailing whitespace.
    text = "\n".join(line.rstrip() for line in lines).rstrip() + "\n"
    return text


# ---------------------------------------------------------------------------
# Output organization
# ---------------------------------------------------------------------------


def module_output_path(module: ModuleInfo) -> Path:
    """Map a module's dotted name to its MDX output path.

    Docusaurus treats ``foo/foo.mdx`` as the index of ``foo/`` — that
    collides with our explicit ``foo/index.mdx``. When a leaf module
    shares its parent package's name (e.g. ``models.file_database``
    inside the ``file_database`` package), we suffix the file name to
    avoid the collision.
    """
    rel = module.dotted_name[len(PACKAGE_DOTTED) + 1:]
    parts = rel.split(".") if rel else []

    if module.rel_path.name == "__init__.py":
        # Subpackage __init__: write to <subpackage>/index.mdx
        if not parts:
            return API_DOCS_ROOT / "index.mdx"
        return API_DOCS_ROOT.joinpath(*parts) / "index.mdx"
    else:
        # parts looks like ['services', 'app_users', 'django_user_services']
        if len(parts) == 1:
            # Top-level module like utilities.py or handlers.py
            return API_DOCS_ROOT / f"{parts[0]}.mdx"
        leaf = parts[-1]
        parent = parts[-2]
        if leaf == parent:
            leaf = f"{leaf}-module"
        return API_DOCS_ROOT.joinpath(*parts[:-1]) / f"{leaf}.mdx"


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    # Force LF line endings, no trailing whitespace per line.
    normalized = "\n".join(line.rstrip() for line in text.splitlines())
    if not normalized.endswith("\n"):
        normalized += "\n"
    path.write_text(normalized, encoding="utf-8", newline="\n")


def write_category(dir_path: Path, label: str, position: int) -> None:
    """Write a Docusaurus _category_.json for a directory.

    If the directory has its own ``index.mdx`` we DO NOT add a
    ``generated-index`` link — that would collide with the file's URL.
    Sidebar collapsing and labelling still work without it.
    """
    payload: dict = {
        "label": label,
        "position": position,
    }
    text = json.dumps(payload, indent=2, sort_keys=False) + "\n"
    write_text(dir_path / "_category_.json", text)


def render_subpackage_index(
    dotted_name: str,
    module: ModuleInfo,
    children: list[tuple[str, str]],  # (label, link target relative to dir)
) -> str:
    """Render a package's ``index.mdx`` from its ``__init__.py`` module.

    Includes the module-level docstring, any classes/functions defined
    in ``__init__.py`` itself, and a "Modules" section listing each
    sibling submodule and subpackage.
    """
    short = dotted_name[len(PACKAGE_DOTTED) + 1:]
    lines: list[str] = []
    lines.append("---")
    lines.append(f"id: {short}.index" if short else "id: index")
    lines.append(f"title: {dotted_name}")
    lines.append("sidebar_label: Overview")
    lines.append("sidebar_position: 0")
    lines.append("---")
    lines.append("")
    lines.append(f"# `{dotted_name}`")
    lines.append("")
    if module.docstring:
        lines.append(escape_mdx_text(module.docstring))
    else:
        lines.append("> _No description._")
        lines.append("")

    if module.classes:
        lines.append("## Classes")
        lines.append("")
        for cls in module.classes:
            lines.extend(_render_class(cls, dotted_name))
            lines.append("")

    if module.functions:
        lines.append("## Functions")
        lines.append("")
        for func in module.functions:
            anchor = heading_id(func.name)
            lines.extend(_render_function(func, anchor, level=3))
            lines.append("")

    if children:
        lines.append("## Modules")
        lines.append("")
        for label, target in sorted(children):
            # Use the .mdx extension so Docusaurus resolves the link
            # relative to the source file's path, not the rendered URL
            # (which omits trailing slashes and breaks ./<sibling>).
            lines.append(f"- [`{label}`]({target})")
        lines.append("")

    text = "\n".join(line.rstrip() for line in lines).rstrip() + "\n"
    return text


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def clean_output_dir() -> None:
    if API_DOCS_ROOT.exists():
        for child in API_DOCS_ROOT.iterdir():
            if child.is_file():
                child.unlink()
            elif child.is_dir():
                shutil.rmtree(child)
    else:
        API_DOCS_ROOT.mkdir(parents=True, exist_ok=True)


def collect_modules() -> list[ModuleInfo]:
    modules: list[ModuleInfo] = []
    # Walk only the configured top-level targets.
    for target in sorted(TOP_LEVEL_TARGETS):
        target_path = PACKAGE_ROOT / target
        if target.endswith(".py"):
            if not target_path.is_file():
                print(f"Missing top-level module: {target_path}", file=sys.stderr)
                continue
            dotted = f"{PACKAGE_DOTTED}.{target_path.stem}"
            info = parse_module(target_path, dotted)
            if info is not None:
                modules.append(info)
        else:
            if not target_path.is_dir() or not (target_path / "__init__.py").exists():
                print(
                    f"Skipping {target}: not a Python package (no __init__.py).",
                    file=sys.stderr,
                )
                continue
            for path, dotted_name in iter_modules(
                target_path, f"{PACKAGE_DOTTED}.{target}"
            ):
                info = parse_module(path, dotted_name)
                if info is None:
                    continue
                modules.append(info)
    modules.sort(key=lambda m: m.dotted_name)
    return modules


def main() -> int:
    clean_output_dir()
    modules = collect_modules()

    # Track per-directory children for subpackage index pages.
    # Map dir-path -> list of (label, slug)
    dir_children: dict[Path, list[tuple[str, str]]] = {}
    # Map dotted package name -> (dir_path, ModuleInfo for __init__.py)
    package_init: dict[str, tuple[Path, ModuleInfo]] = {}

    written_files = 0
    module_count = 0

    for module in modules:
        out_path = module_output_path(module)
        is_init = module.rel_path.name == "__init__.py"
        text = render_module(module)
        write_text(out_path, text)
        written_files += 1
        module_count += 1

        if is_init:
            package_init[module.dotted_name] = (out_path.parent, module)
        else:
            parent_dir = out_path.parent
            short_label = out_path.stem
            dir_children.setdefault(parent_dir, []).append((short_label, short_label))

    # Each sub-package directory gets a _category_.json (alphabetic ordering).
    sorted_dirs = sorted({p for p in dir_children.keys()} | {p for p, _ in package_init.values()})
    for position, dir_path in enumerate(sorted_dirs, start=1):
        if dir_path == API_DOCS_ROOT:
            continue
        label = dir_path.name
        write_category(dir_path, label, position)

    # Root: build a top-level index.mdx that links to each top-level subpackage / module.
    root_children: list[tuple[str, str]] = []
    # Top-level: every entry directly under API_DOCS_ROOT
    for entry in sorted(API_DOCS_ROOT.iterdir()):
        if entry.is_dir():
            index_file = entry / "index.mdx"
            if index_file.exists():
                root_children.append((entry.name, f"./{entry.name}/index.mdx"))
        elif entry.is_file() and entry.suffix == ".mdx" and entry.stem != "index":
            root_children.append((entry.stem, f"./{entry.name}"))

    root_text_lines: list[str] = []
    root_text_lines.append("---")
    root_text_lines.append("id: index")
    root_text_lines.append("title: API Reference")
    root_text_lines.append("sidebar_label: Overview")
    root_text_lines.append("sidebar_position: 1")
    root_text_lines.append("slug: /api")
    root_text_lines.append("---")
    root_text_lines.append("")
    root_text_lines.append("# API Reference")
    root_text_lines.append("")
    root_text_lines.append(
        "Reference documentation for the public modules in "
        "`tethysext.atcore`. Pages here are generated directly from "
        "the project source by `website/scripts/generate_api_docs.py`. "
        "Edit Python docstrings, not these files."
    )
    root_text_lines.append("")
    root_text_lines.append("## Subpackages and modules")
    root_text_lines.append("")
    for label, target in sorted(root_children):
        root_text_lines.append(f"- [`{label}`]({target})")
    root_text_lines.append("")
    root_text = "\n".join(root_text_lines).rstrip() + "\n"
    write_text(API_DOCS_ROOT / "index.mdx", root_text)
    # Remove the leftover placeholder index.md if present.
    placeholder = API_DOCS_ROOT / "index.md"
    if placeholder.exists():
        placeholder.unlink()

    # Now overwrite each subpackage __init__ render with a richer index
    # that includes both the module's own classes/functions AND a list
    # of sibling submodules.
    for dotted_name, (dir_path, init_module) in package_init.items():
        children: list[tuple[str, str]] = []
        for entry in sorted(dir_path.iterdir()):
            if entry.is_dir():
                index_file = entry / "index.mdx"
                if index_file.exists():
                    children.append((entry.name, f"./{entry.name}/index.mdx"))
            elif entry.is_file() and entry.suffix == ".mdx" and entry.stem != "index":
                children.append((entry.stem, f"./{entry.name}"))
        index_text = render_subpackage_index(
            dotted_name=dotted_name,
            module=init_module,
            children=children,
        )
        write_text(dir_path / "index.mdx", index_text)

    # Re-write root category.json (no explicit link — index.mdx handles it).
    root_cat = {
        "label": "API Reference",
        "position": 99,
    }
    write_text(API_DOCS_ROOT / "_category_.json", json.dumps(root_cat, indent=2) + "\n")

    print(f"Generated docs for {module_count} modules into {API_DOCS_ROOT}")
    print(f"Total files written: {written_files} (plus index/category files)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
