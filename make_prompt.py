#!/usr/bin/env python3
# make_prompt.py
from __future__ import annotations
import os, sys, subprocess, io
from pathlib import Path
from typing import Iterable, List, Set, Tuple

ROOT = Path.cwd()
OUTFILE = ROOT / "workspace.prompt"
GITIGNORE = ROOT / ".gitignore"

def has_git_repo() -> bool:
    return (ROOT / ".git").exists()

def load_pathspec():
    try:
        import pathspec  # type: ignore
        spec = None
        if GITIGNORE.exists():
            with GITIGNORE.open("r", encoding="utf-8") as f:
                spec = pathspec.PathSpec.from_lines(pathspec.patterns.GitWildMatchPattern, f)
        return spec
    except Exception:
        return None

def list_files_with_git() -> List[Path]:
    # all tracked + untracked, excluding ignored by .gitignore/.git/info/exclude/global excludes
    cmd = ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"]
    try:
        out = subprocess.check_output(cmd, cwd=ROOT)
        rels = [Path(p) for p in out.decode("utf-8", "ignore").split("\x00") if p]
        return [ROOT / p for p in rels]
    except Exception:
        return []

def list_files_with_pathspec(spec) -> List[Path]:
    files: List[Path] = []
    for dirpath, dirnames, filenames in os.walk(ROOT, topdown=True):
        # prune .git early
        dirnames[:] = [d for d in dirnames if d != ".git"]
        for name in filenames:
            p = Path(dirpath) / name
            rel = p.relative_to(ROOT).as_posix()
            if spec and spec.match_file(rel):
                continue
            files.append(p)
    return files

def list_all_files_fallback() -> List[Path]:
    files: List[Path] = []
    for dirpath, dirnames, filenames in os.walk(ROOT, topdown=True):
        dirnames[:] = [d for d in dirnames if d != ".git"]
        for name in filenames:
            files.append(Path(dirpath) / name)
    return files

def is_probably_text(path: Path, blocksize: int = 4096) -> bool:
    try:
        with open(path, "rb") as f:
            b = f.read(blocksize)
        if b == b"":
            return True
        # Heuristic: no NUL bytes, decodable as UTF-8 (with small error rate)
        if b"\x00" in b:
            return False
        try:
            b.decode("utf-8")
            return True
        except UnicodeDecodeError:
            # allow if most bytes are ASCII
            ascii_ratio = sum(1 for x in b if 9 <= x <= 127) / max(1, len(b))
            return ascii_ratio > 0.9
    except Exception:
        return False

def render_tree(paths: Iterable[Path]) -> str:
    rels = sorted([p.relative_to(ROOT) for p in paths], key=lambda p: p.as_posix())
    # Build a directory tree map
    tree = {}
    for r in rels:
        parts = r.parts
        cur = tree
        for i, part in enumerate(parts):
            key = ("F", part) if i == len(parts)-1 and not (ROOT / r).is_dir() else ("D", part)
            cur = cur.setdefault(key, {})
    lines: List[str] = []
    def walk(node, prefix=""):
        items = sorted(node.items(), key=lambda kv: (kv[0][0], kv[0][1].lower()))
        for i, ((kind, name), child) in enumerate(items):
            connector = "└── " if i == len(items)-1 else "├── "
            lines.append(prefix + connector + name)
            if child:
                new_prefix = prefix + ("    " if i == len(items)-1 else "│   ")
                walk(child, new_prefix)
    lines.insert(0, ROOT.name)
    walk(tree, "")
    return "\n".join(lines)

def main():
    # 1) decide file set using best available method
    files: List[Path] = []
    if has_git_repo():
        files = list_files_with_git()
    if not files:
        spec = load_pathspec()
        if spec:
            files = list_files_with_pathspec(spec)
        else:
            files = list_all_files_fallback()

    # Exclude the output file itself and obvious binary blobs by extension
    skip_ext = {
        ".png",".jpg",".jpeg",".webp",".gif",".bmp",".ico",".svg",
        ".pdf",".zip",".tar",".gz",".xz",".7z",".rar",
        ".mp3",".wav",".flac",".aac",".mp4",".mov",".mkv",".avi",
        ".ttf",".otf",".woff",".woff2",".psd",".ai",".pptx",".docx",".xlsx",
        ".pt",".bin",".npy",".npz",".so",".dylib",".dll",
    }
    files = [p for p in files if p.is_file() and p.resolve() != OUTFILE.resolve() and p.suffix.lower() not in skip_ext]

    # 2) produce file tree using included files plus their parent dirs
    tree_sources = set()
    for p in files:
        q = p
        while True:
            tree_sources.add(q)
            if q.parent == ROOT or q.parent == q:
                tree_sources.add(q.parent)
                break
            q = q.parent
    tree_text = render_tree([q for q in tree_sources if q.exists()])

    # 3) write output
    with io.open(OUTFILE, "w", encoding="utf-8", newline="\n") as out:
        out.write("# FILE TREE\n")
        out.write(tree_text)
        out.write("\n\n")
        for path in sorted(files, key=lambda x: x.relative_to(ROOT).as_posix()):
            rel = path.relative_to(ROOT).as_posix()
            if not is_probably_text(path):
                continue
            out.write(rel + "\n")
            try:
                with io.open(path, "r", encoding="utf-8", errors="replace") as f:
                    out.write(f.read())
            except Exception as e:
                out.write(f"[UNREADABLE: {e}]\n")
            out.write("\n")  # separator between files

    print(f"Wrote {OUTFILE}")

if __name__ == "__main__":
    main()