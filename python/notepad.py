import argparse
import ast
import base64
import binascii
import bisect
import builtins
import code
import codecs
import contextlib
import csv
import datetime
import difflib
import filecmp
import fnmatch
import ftplib
import hashlib
import html
import http.server
import importlib.util
import inspect
import io
import json
import math
import operator
import os
import pydoc
import queue
import random
import re
import secrets
import shlex
import shutil
import socket
import sqlite3
import string
import subprocess
import sys
import tempfile
import textwrap
import threading
import time
import traceback
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
import uuid
import webbrowser
import xml.dom.minidom
import zipfile
from pathlib import Path
from xml.parsers.expat import ExpatError
import tkinter as tk
import tkinter.font as tkfont
from tkinter import colorchooser, filedialog, messagebox, simpledialog, ttk

try:
    import tomllib
except ImportError:
    tomllib = None

APP = "Notepad"
VERSION = "4.0"


def find_script_path():
    path = globals().get("__file__")
    if not path:
        candidate = sys.argv[0] if sys.argv else ""
        if candidate and os.path.isfile(candidate) and \
                candidate.lower().endswith((".py", ".pyw", ".pyz")):
            path = candidate
    return os.path.abspath(path) if path else None


SCRIPT_PATH = find_script_path()
SCRIPT_DIR = os.path.dirname(SCRIPT_PATH) if SCRIPT_PATH else os.getcwd()
PORTABLE_DIR = os.path.join(SCRIPT_DIR, "notepad_data")
HOME_CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".pynotepad")
NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)


def configure_paths(base):
    global CONFIG_DIR, CONFIG_FILE, RECOVERY_DIR, SNIPPETS_FILE, HISTORY_DIR, UNDO_DIR
    global KEYBINDINGS_FILE, THEMES_FILE, TEMPLATES_DIR, SCRATCH_FILE, ERROR_LOG, INSTANCE_FILE
    CONFIG_DIR = base
    CONFIG_FILE = os.path.join(base, "config.json")
    RECOVERY_DIR = os.path.join(base, "recovery")
    SNIPPETS_FILE = os.path.join(base, "snippets.json")
    HISTORY_DIR = os.path.join(base, "history")
    UNDO_DIR = os.path.join(base, "undo")
    KEYBINDINGS_FILE = os.path.join(base, "keybindings.json")
    THEMES_FILE = os.path.join(base, "themes.json")
    TEMPLATES_DIR = os.path.join(base, "templates")
    SCRATCH_FILE = os.path.join(base, "scratchpad.txt")
    ERROR_LOG = os.path.join(base, "error.log")
    INSTANCE_FILE = os.path.join(base, "instance.json")


configure_paths(PORTABLE_DIR if os.path.isdir(PORTABLE_DIR) else HOME_CONFIG_DIR)

ENCODINGS = ("utf-8", "utf-8-sig", "utf-16", "cp1252", "latin-1")
EOLS = {"LF": "\n", "CRLF": "\r\n", "CR": "\r"}
EOL_NAMES = {v: k for k, v in EOLS.items()}
DEFAULT_EOL = "\r\n" if sys.platform == "win32" else "\n"

MAX_RECENT = 10
HIGHLIGHT_LIMIT = 500_000
BRACKET_LIMIT = 50_000
OCCURRENCE_LIMIT = 2_000
FIND_ALL_LIMIT = 5_000
RECOVERY_INTERVAL = 30_000
DISK_CHECK_INTERVAL = 2_000
AUTO_SAVE_INTERVAL = 30_000
LARGE_FILE = 20 * 1024 * 1024
LARGE_CHUNK = 2 * 1024 * 1024
HEX_CHUNK = 64 * 1024
FIF_MAX_FILE = 5 * 1024 * 1024
FIF_MAX_RESULTS = 5_000
HISTORY_KEEP = 30
UNDO_SNAPSHOTS = 40
UNDO_MAX_DOC = 1024 * 1024
CLIP_HISTORY = 30
GIT_MAX_LINES = 20_000
SKIP_DIRS = {".git", ".hg", ".svn", "node_modules", "__pycache__", ".venv", "venv",
             ".idea", ".vs", ".mypy_cache", ".pytest_cache"}
MIN_SIZE, MAX_SIZE = 6, 48

if sys.platform == "win32":
    DEFAULT_FONT = "Consolas"
elif sys.platform == "darwin":
    DEFAULT_FONT = "Menlo"
else:
    DEFAULT_FONT = "DejaVu Sans Mono"
DEFAULT_SIZE = 11

BG = "#001040"
FG = "#FFFFFF"
THEMES = {
    "Blue": {
        "bg": BG, "fg": FG, "sel_bg": FG, "sel_fg": BG, "cursor": FG,
        "gutter_bg": "#000A2A", "gutter_fg": "#6070A0",
        "status_bg": "#C0C0C0", "status_fg": "#000000", "bracket": "#3050A0",
        "curline": "#0A1C55", "occur": "#24407A", "bookmark": "#FFFF55",
        "diff_add": "#55FF55", "diff_del": "#FF7777", "diff_hunk": "#55FFFF",
        "comment": "#8C9CC0", "string": "#55FF55", "number": "#FF77FF",
        "keyword": "#FFFF55", "builtin": "#55FFFF", "function": "#FFD080",
        "klass": "#FFD080", "decorator": "#FF9955", "operator": "#FFFFFF",
    },
    "Dark": {
        "bg": "#1E1E1E", "fg": "#D4D4D4", "sel_bg": "#264F78", "sel_fg": "#FFFFFF",
        "cursor": "#AEAFAD", "gutter_bg": "#1E1E1E", "gutter_fg": "#858585",
        "status_bg": "#007ACC", "status_fg": "#FFFFFF", "bracket": "#4A4D55",
        "curline": "#2A2A2A", "occur": "#3A4048", "bookmark": "#E5C07B",
        "diff_add": "#89D185", "diff_del": "#F48771", "diff_hunk": "#569CD6",
        "comment": "#6A9955", "string": "#CE9178", "number": "#B5CEA8",
        "keyword": "#569CD6", "builtin": "#4EC9B0", "function": "#DCDCAA",
        "klass": "#4EC9B0", "decorator": "#C586C0", "operator": "#D4D4D4",
    },
    "Light": {
        "bg": "#FFFFFF", "fg": "#000000", "sel_bg": "#ADD6FF", "sel_fg": "#000000",
        "cursor": "#000000", "gutter_bg": "#F3F3F3", "gutter_fg": "#999999",
        "status_bg": "#E0E0E0", "status_fg": "#000000", "bracket": "#C8E1FF",
        "curline": "#F2F6FC", "occur": "#E2E8F0", "bookmark": "#C79500",
        "diff_add": "#098658", "diff_del": "#C72E2E", "diff_hunk": "#0000FF",
        "comment": "#008000", "string": "#A31515", "number": "#098658",
        "keyword": "#0000FF", "builtin": "#267F99", "function": "#795E26",
        "klass": "#267F99", "decorator": "#AF00DB", "operator": "#000000",
    },
}

TOKEN_GROUP_NAMES = ("comment", "string", "number", "keyword", "builtin",
                     "function", "klass", "decorator", "operator", "error", "warning")


def _words(names, ignore_case=False):
    body = r"\b(?:" + "|".join(names.split()) + r")\b"
    return f"(?i:{body})" if ignore_case else body


def _language(*rules):
    return re.compile("|".join(f"(?P<{group}_{i}>{pattern})"
                               for i, (group, pattern) in enumerate(rules)), re.MULTILINE)


STR_DQ = r'"(?:\\.|[^"\\\n])*"?'
STR_SQ = r"'(?:\\.|[^'\\\n])*'?"
NUMBER = r"\b(?:0[xX][0-9a-fA-F_]+|0[bB][01_]+|\d[\d_]*(?:\.\d+)?(?:[eE][+-]?\d+)?)[jJlLfFuU]*\b"

PY_KEYWORDS = ("False None True and as assert async await break class continue def del elif "
               "else except finally for from global if import in is lambda nonlocal not or "
               "pass raise return try while with yield")
PY_BUILTINS = ("self cls print len range str int float bool bytes list dict set tuple frozenset "
               "open type isinstance issubclass super enumerate zip map filter sorted reversed "
               "min max sum abs round any all input repr hash id iter next getattr setattr "
               "hasattr delattr callable vars dir format chr ord object property staticmethod "
               "classmethod Exception ValueError TypeError KeyError IndexError AttributeError "
               "RuntimeError OSError ImportError StopIteration NotImplementedError __name__")
CLIKE_KEYWORDS = (
    "abstract as async await auto break case catch char class const constexpr continue "
    "default defer delete do double else elseif enum export extends extern false final finally "
    "float fn for foreach from func function go goto if impl implements import in instanceof "
    "int interface internal let long loop match mod module mut namespace new nil null nullptr "
    "override package private protected pub public readonly ref return select short signed "
    "sizeof static struct super switch synchronized template this throw throws trait true try "
    "type typedef typeof undefined union unsafe unsigned use using var virtual void volatile "
    "where while with yield bool boolean string byte echo require require_once")
CLIKE_BUILTINS = ("console window document Math JSON Object Array String Number Promise Map Set "
                  "Error System std printf malloc free Vec Option Some None Ok Err fmt len make "
                  "append println print")
SQL_KEYWORDS = (
    "select from where and or not insert into values update set delete create alter drop "
    "table view index primary key foreign references join inner left right outer full cross "
    "on as group by order having limit offset distinct union all exists in is null like "
    "between case when then else end begin commit rollback transaction declare procedure "
    "function return returns if while database schema default unique check constraint asc "
    "desc top with grant revoke int integer varchar char text date datetime timestamp "
    "boolean float decimal numeric bigint")
SHELL_KEYWORDS = ("if then else elif fi for do done while until case esac in function return "
                  "export local readonly source exit break continue shift set unset echo cd test")
BATCH_KEYWORDS = ("echo set if else goto call for in do exist not errorlevel defined equ neq lss "
                  "leq gtr geq setlocal endlocal enabledelayedexpansion exit pause cls cd pushd "
                  "popd mkdir rmdir del copy move start title shift off on nul")


def _clike(preprocessor=False):
    rules = [
        ("comment", r"//[^\n]*|/\*[\s\S]*?(?:\*/|\Z)"),
        ("string", STR_DQ + "|" + STR_SQ + r"|`(?:\\.|[^`\\])*`?"),
    ]
    if preprocessor:
        rules.append(("decorator", r"^[ \t]*#[ \t]*\w+"))
    rules += [
        ("decorator", r"@[A-Za-z_]\w*"),
        ("builtin", r"\$\w+"),
        ("klass", r"(?<=class )\w+|(?<=struct )\w+|(?<=interface )\w+"),
        ("keyword", _words(CLIKE_KEYWORDS)),
        ("builtin", _words(CLIKE_BUILTINS)),
        ("function", r"\b[A-Za-z_]\w*(?=\s*\()"),
        ("number", NUMBER),
    ]
    return _language(*rules)


LANGUAGES = {
    "python": _language(
        ("comment", r"#[^\n]*"),
        ("string", r"(?:\b[rRbBuUfF]{1,2})?(?:'''[\s\S]*?(?:'''|\Z)|\"\"\"[\s\S]*?(?:\"\"\"|\Z)|"
                   + STR_DQ + "|" + STR_SQ + ")"),
        ("decorator", r"@[A-Za-z_][\w.]*"),
        ("function", r"(?<=def )[A-Za-z_]\w*"),
        ("klass", r"(?<=class )[A-Za-z_]\w*"),
        ("keyword", _words(PY_KEYWORDS)),
        ("builtin", _words(PY_BUILTINS)),
        ("number", NUMBER),
    ),
    "clike": _clike(),
    "c": _clike(preprocessor=True),
    "json": _language(
        ("builtin", r'"(?:\\.|[^"\\\n])*"(?=\s*:)'),
        ("string", STR_DQ),
        ("keyword", _words("true false null")),
        ("number", r"-?\b\d+(?:\.\d+)?(?:[eE][+-]?\d+)?\b"),
    ),
    "markup": _language(
        ("comment", r"<!--[\s\S]*?(?:-->|\Z)"),
        ("string", r"<!\[CDATA\[[\s\S]*?(?:\]\]>|\Z)"),
        ("decorator", r"<[!?][^>]*>?"),
        ("keyword", r"</?[A-Za-z][\w:.-]*|/?>"),
        ("builtin", r"\b[\w:-]+(?==)"),
        ("string", r"(?<==)\"[^\"]*\"?|(?<==)'[^']*'?"),
        ("number", r"&#?\w+;"),
    ),
    "css": _language(
        ("comment", r"/\*[\s\S]*?(?:\*/|\Z)"),
        ("string", STR_DQ + "|" + STR_SQ),
        ("keyword", r"@[\w-]+|!important"),
        ("number", r"#[0-9a-fA-F]{3,8}\b|-?\b\d+(?:\.\d+)?"
                   r"(?:px|em|rem|vh|vw|vmin|vmax|ch|pt|deg|ms|s|fr|%)?"),
        ("builtin", r"[\w-]+(?=\s*:[^\n{]*;)"),
        ("function", r"\b[\w-]+(?=\()"),
    ),
    "ini": _language(
        ("comment", r"^[ \t]*[;#][^\n]*"),
        ("keyword", r"^[ \t]*\[[^\]\n]*\]"),
        ("builtin", r"^[ \t]*[^\s=:;#\[][^=:\n]*?(?=[ \t]*[=:])"),
        ("string", STR_DQ),
        ("keyword", _words("true false yes no on off", ignore_case=True)),
        ("number", r"\b\d+(?:\.\d+)?\b"),
    ),
    "sql": _language(
        ("comment", r"--[^\n]*|/\*[\s\S]*?(?:\*/|\Z)"),
        ("string", r"'(?:''|[^'])*'?"),
        ("builtin", r'"[^"\n]*"|`[^`\n]*`|\[[^\]\n]*\]'),
        ("keyword", _words(SQL_KEYWORDS, ignore_case=True)),
        ("function", r"\b\w+(?=\s*\()"),
        ("number", NUMBER),
    ),
    "shell": _language(
        ("comment", r"(?:^|(?<=[ \t]))#[^\n]*"),
        ("string", r'"(?:\\.|[^"\\])*"?|' + r"'[^']*'?"),
        ("builtin", r"\$\{[^}\n]*\}?|\$(?:\w+|[@#?$!*-])"),
        ("keyword", _words(SHELL_KEYWORDS)),
        ("function", r"^[ \t]*[A-Za-z_]\w*(?=\s*\(\))"),
        ("number", r"\b\d+\b"),
    ),
    "batch": _language(
        ("comment", r"^[ \t]*(?:(?i:rem)\b|::)[^\n]*"),
        ("function", r"^[ \t]*:\w+"),
        ("string", r'"[^"\n]*"?'),
        ("builtin", r"%%?~?\w+%?|!\w+!"),
        ("keyword", _words(BATCH_KEYWORDS, ignore_case=True)),
        ("number", r"\b\d+\b"),
    ),
    "markdown": _language(
        ("string", r"^```[\s\S]*?(?:^```[^\n]*|\Z)"),
        ("keyword", r"^#{1,6}[ \t][^\n]*"),
        ("comment", r"^>[^\n]*"),
        ("string", r"`[^`\n]+`"),
        ("function", r"\*\*[^*\n]+\*\*|__[^_\n]+__"),
        ("builtin", r"!?\[[^\]\n]*\]\([^)\n]*\)"),
        ("number", r"^[ \t]*(?:[-*+]|\d+\.)(?=[ \t])"),
    ),
}

EXTENSIONS = {}
for _lang, _exts in (
        ("python", "py pyw"),
        ("clike", "js mjs cjs jsx ts tsx java go rs php kt kts swift dart scala groovy"),
        ("c", "c h cpp hpp cc cxx hh cs m"),
        ("json", "json jsonc"),
        ("markup", "html htm xhtml xml svg xaml xsl xslt csproj vbproj config plist"),
        ("css", "css scss less"),
        ("ini", "ini cfg conf toml properties env gitconfig editorconfig reg"),
        ("sql", "sql"),
        ("shell", "sh bash zsh ksh bashrc zshrc profile"),
        ("batch", "bat cmd"),
        ("markdown", "md markdown")):
    for _ext in _exts.split():
        EXTENSIONS[_ext] = _lang

AUTO_INDENT_OPENERS = {"python": (":", "(", "[", "{")}
for _lang in ("clike", "c", "json", "css", "shell"):
    AUTO_INDENT_OPENERS[_lang] = ("{", "(", "[")


def detect_language(path):
    if not path:
        return None
    base = os.path.basename(path).lower()
    if base in ("dockerfile", "containerfile") or base.startswith("dockerfile."):
        return "dockerfile"
    if base in ("makefile", "gnumakefile"):
        return "makefile"
    ext = os.path.splitext(base)[1].lstrip(".")
    if not ext:
        ext = base.lstrip(".")
    return EXTENSIONS.get(ext)


COMMENT_STYLES = {
    None: ("#", ""), "python": ("#", ""), "shell": ("#", ""), "ini": ("#", ""),
    "clike": ("//", ""), "c": ("//", ""), "sql": ("--", ""), "batch": ("REM", ""),
    "css": ("/*", "*/"), "markup": ("<!--", "-->"), "markdown": ("<!--", "-->"),
}
PAIRS = {"(": ")", "[": "]", "{": "}", '"': '"', "'": "'", "`": "`"}
OPEN_KEYS = {"(": "parenleft", "[": "bracketleft", "{": "braceleft",
             '"': "quotedbl", "'": "apostrophe", "`": "grave"}
CLOSE_KEYS = {")": "parenright", "]": "bracketright", "}": "braceright"}
STRING_PREFIXES = ("f", "r", "b", "u", "rb", "br", "fr", "rf")

DEFAULT_SNIPPETS = {
    "python": {
        "main": 'if __name__ == "__main__":\n    $0',
        "def": "def name($0):\n    pass",
        "class": "class Name:\n    def __init__(self$0):\n        pass",
        "for": "for item in $0:\n    pass",
        "while": "while $0:\n    pass",
        "try": "try:\n    $0\nexcept Exception as error:\n    print(error)",
        "with": 'with open($0, encoding="utf-8") as f:\n    data = f.read()',
    },
    "clike": {
        "for": "for (let i = 0; i < $0; i++) {\n    \n}",
        "if": "if ($0) {\n    \n}",
        "func": "function name($0) {\n    \n}",
        "log": "console.log($0);",
        "try": "try {\n    $0\n} catch (error) {\n    console.error(error);\n}",
    },
    "c": {
        "for": "for (int i = 0; i < $0; i++) {\n    \n}",
        "if": "if ($0) {\n    \n}",
        "main": "int main(void) {\n    $0\n    return 0;\n}",
        "inc": "#include <$0>",
    },
    "markup": {
        "html": ('<!DOCTYPE html>\n<html lang="en">\n<head>\n    <meta charset="utf-8">\n'
                 '    <meta name="viewport" content="width=device-width, initial-scale=1">\n'
                 '    <title>$0</title>\n</head>\n<body>\n    \n</body>\n</html>'),
        "a": '<a href="$0"></a>',
        "div": '<div class="$0"></div>',
        "img": '<img src="$0" alt="">',
    },
    "css": {
        "media": "@media (max-width: $0px) {\n    \n}",
        "flex": "display: flex;\nalign-items: center;\njustify-content: $0;",
    },
    "markdown": {
        "table": "| Column 1 | Column 2 |\n|----------|----------|\n| $0 |  |",
        "link": "[$0](https://)",
        "code": "```\n$0\n```",
        "img": "![$0](image.png)",
    },
    "sql": {
        "sel": "SELECT $0\nFROM table\nWHERE condition;",
        "ins": "INSERT INTO table (columns)\nVALUES ($0);",
    },
    "shell": {
        "if": "if [ $0 ]; then\n    \nfi",
        "for": "for item in $0; do\n    \ndone",
        "bash": "#!/usr/bin/env bash\nset -euo pipefail\n\n$0",
    },
    "*": {
        "lorem": ("Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod "
                  "tempor incididunt ut labore et dolore magna aliqua.$0"),
    },
}

RUNNERS = {
    ".js": [["node"]], ".mjs": [["node"]], ".cjs": [["node"]],
    ".sh": [["bash"], ["sh"]], ".bash": [["bash"]], ".zsh": [["zsh"]],
    ".rb": [["ruby"]], ".pl": [["perl"]], ".php": [["php"]], ".lua": [["lua"]],
    ".go": [["go", "run"]], ".java": [["java"]], ".r": [["Rscript"]],
    ".ps1": [["pwsh", "-File"], ["powershell", "-ExecutionPolicy", "Bypass", "-File"]],
    ".bat": [["cmd", "/c"]], ".cmd": [["cmd", "/c"]],
}

DEFAULT_CONFIG = {
    "font_family": DEFAULT_FONT, "font_size": DEFAULT_SIZE,
    "wrap": False, "auto_indent": True, "line_numbers": True, "highlight": True,
    "theme": "Blue", "geometry": "900x600", "maximized": False, "recent": [],
    "match_case": False, "whole_word": False, "regex": False,
    "tab_width": 4, "use_spaces": True, "auto_close": True, "highlight_line": True,
    "highlight_occurrences": True, "trim_on_save": False, "restore_session": True,
    "session": {},
}


def load_config():
    cfg = dict(DEFAULT_CONFIG)
    try:
        with open(CONFIG_FILE, encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            cfg.update(data)
    except (OSError, ValueError):
        pass
    return cfg


def decode_bytes(data, forced=None):
    if forced:
        return data.decode(forced, errors="replace"), forced
    if data.startswith(codecs.BOM_UTF8):
        return data[len(codecs.BOM_UTF8):].decode("utf-8", errors="replace"), "utf-8-sig"
    if data.startswith((codecs.BOM_UTF16_LE, codecs.BOM_UTF16_BE)):
        return data.decode("utf-16", errors="replace"), "utf-16"
    for enc in ("utf-8", "cp1252"):
        try:
            return data.decode(enc), enc
        except UnicodeDecodeError:
            continue
    return data.decode("latin-1"), "latin-1"


def looks_binary(data):
    if data.startswith((codecs.BOM_UTF16_LE, codecs.BOM_UTF16_BE)):
        return False
    return b"\x00" in data[:8192]


def detect_eol(text):
    if "\r\n" in text:
        return "\r\n"
    if "\r" in text:
        return "\r"
    if "\n" in text:
        return "\n"
    return DEFAULT_EOL


def make_indexer(content):
    starts = [0]
    pos = content.find("\n")
    while pos != -1:
        starts.append(pos + 1)
        pos = content.find("\n", pos + 1)

    def index(offset):
        line = bisect.bisect_right(starts, offset) - 1
        return f"{line + 1}.{offset - starts[line]}"
    return index


def selected_lines(widget):
    if widget.tag_ranges("sel"):
        first = int(widget.index("sel.first").split(".")[0])
        last_index = widget.index("sel.last")
        last = int(last_index.split(".")[0])
        if last > first and last_index.endswith(".0"):
            last -= 1
        return first, last
    line = int(widget.index("insert").split(".")[0])
    return line, line


class ToolError(Exception):
    def __init__(self, message, line=None):
        super().__init__(message)
        self.line = line


_BIN_OPS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
            ast.Div: operator.truediv, ast.FloorDiv: operator.floordiv,
            ast.Mod: operator.mod, ast.Pow: operator.pow}
_UNARY_OPS = {ast.UAdd: operator.pos, ast.USub: operator.neg}
_CALC_NAMES = {"pi": math.pi, "e": math.e, "tau": math.tau}
_CALC_FUNCS = {"sqrt": math.sqrt, "sin": math.sin, "cos": math.cos, "tan": math.tan,
               "asin": math.asin, "acos": math.acos, "atan": math.atan,
               "log": math.log, "log10": math.log10, "log2": math.log2, "exp": math.exp,
               "abs": abs, "round": round, "floor": math.floor, "ceil": math.ceil,
               "min": min, "max": max}


def safe_eval(expression):
    expression = expression.replace("^", "**").replace("×", "*").replace("÷", "/")
    tree = ast.parse(expression.strip(), mode="eval")

    def ev(node):
        if isinstance(node, ast.Expression):
            return ev(node.body)
        if isinstance(node, ast.Constant) and type(node.value) in (int, float):
            return node.value
        if isinstance(node, ast.BinOp) and type(node.op) in _BIN_OPS:
            left, right = ev(node.left), ev(node.right)
            if isinstance(node.op, ast.Pow) and abs(right) > 10_000:
                raise ValueError("exponent too large")
            return _BIN_OPS[type(node.op)](left, right)
        if isinstance(node, ast.UnaryOp) and type(node.op) in _UNARY_OPS:
            return _UNARY_OPS[type(node.op)](ev(node.operand))
        if isinstance(node, ast.Name) and node.id in _CALC_NAMES:
            return _CALC_NAMES[node.id]
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                and node.func.id in _CALC_FUNCS and not node.keywords):
            return _CALC_FUNCS[node.func.id](*[ev(a) for a in node.args])
        raise ValueError("unsupported expression")
    return ev(tree)


def format_number(value):
    if isinstance(value, float):
        if value.is_integer() and abs(value) < 1e15:
            return str(int(value))
        return f"{value:.12g}"
    return str(value)


HTML_TEMPLATE = """<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>__TITLE__</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
body { font-family: system-ui, -apple-system, "Segoe UI", sans-serif; max-width: 860px;
       margin: 2rem auto; padding: 0 1rem; line-height: 1.6; color: #222; background: #fff; }
code, pre { font-family: Consolas, Menlo, monospace; background: #f3f3f3; border-radius: 4px; }
code { padding: .1em .3em; } pre { padding: .8em 1em; overflow-x: auto; }
pre code { padding: 0; background: none; }
blockquote { border-left: 4px solid #ccc; margin: 0; padding-left: 1em; color: #555; }
table { border-collapse: collapse; } th, td { border: 1px solid #ccc; padding: .3em .6em; }
img { max-width: 100%; } a { color: #0b66c3; }
@media (prefers-color-scheme: dark) {
  body { color: #ddd; background: #1e1e1e; } code, pre { background: #2b2b2b; }
  blockquote { border-color: #555; color: #aaa; } th, td { border-color: #555; }
  a { color: #6cb6ff; }
}
</style></head><body>
__BODY__
</body></html>
"""


def _md_inline(text):
    codes = []

    def keep(m):
        codes.append(html.escape(m.group(1), quote=False))
        return f"\x00{len(codes) - 1}\x00"

    s = re.sub(r"`([^`]+)`", keep, text)
    s = html.escape(s, quote=False)
    s = re.sub(r'!\[([^\]]*)\]\(([^)\s]+)(?:\s+"[^"]*")?\)',
               lambda m: f'<img alt="{m.group(1)}" src="{m.group(2).replace(chr(34), "%22")}">', s)
    s = re.sub(r'\[([^\]]+)\]\(([^)\s]+)(?:\s+"[^"]*")?\)',
               lambda m: f'<a href="{m.group(2).replace(chr(34), "%22")}">{m.group(1)}</a>', s)
    s = re.sub(r"\*\*(.+?)\*\*|__(.+?)__",
               lambda m: f"<strong>{m.group(1) or m.group(2)}</strong>", s)
    s = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<em>\1</em>", s)
    s = re.sub(r"(?<![\w_])_(?!\s)(.+?)(?<!\s)_(?![\w_])", r"<em>\1</em>", s)
    s = re.sub(r"~~(.+?)~~", r"<del>\1</del>", s)
    return re.sub(r"\x00(\d+)\x00", lambda m: f"<code>{codes[int(m.group(1))]}</code>", s)


def _md_cells(row):
    row = row.strip()
    if row.startswith("|"):
        row = row[1:]
    if row.endswith("|"):
        row = row[:-1]
    return [c.strip() for c in row.split("|")]


def _md_blocks(lines):
    out, para = [], []
    list_tag = [None]

    def flush():
        if para:
            out.append("<p>" + _md_inline(" ".join(para)) + "</p>")
            para.clear()

    def close_list():
        if list_tag[0]:
            out.append(f"</{list_tag[0]}>")
            list_tag[0] = None

    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        if stripped.startswith(("```", "~~~")):
            fence = stripped[:3]
            flush()
            close_list()
            i += 1
            code = []
            while i < len(lines) and not lines[i].strip().startswith(fence):
                code.append(lines[i])
                i += 1
            i += 1
            out.append("<pre><code>" + html.escape("\n".join(code)) + "</code></pre>")
            continue
        if not stripped:
            flush()
            close_list()
            i += 1
            continue
        m = re.match(r"(#{1,6})\s+(.*?)\s*#*\s*$", stripped)
        if m:
            flush()
            close_list()
            level = len(m.group(1))
            out.append(f"<h{level}>{_md_inline(m.group(2))}</h{level}>")
            i += 1
            continue
        if re.fullmatch(r"([-*_])(\s*\1){2,}", stripped):
            flush()
            close_list()
            out.append("<hr>")
            i += 1
            continue
        if stripped.startswith(">"):
            flush()
            close_list()
            quote = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                quote.append(re.sub(r"^\s*>\s?", "", lines[i]))
                i += 1
            out.append("<blockquote>" + _md_blocks(quote) + "</blockquote>")
            continue
        if ("|" in stripped and i + 1 < len(lines) and re.fullmatch(
                r"\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)*\|?", lines[i + 1].strip())):
            flush()
            close_list()
            head = _md_cells(line)
            i += 2
            rows = []
            while i < len(lines) and "|" in lines[i] and lines[i].strip():
                rows.append(_md_cells(lines[i]))
                i += 1
            out.append("<table><thead><tr>"
                       + "".join(f"<th>{_md_inline(c)}</th>" for c in head)
                       + "</tr></thead><tbody>"
                       + "".join("<tr>" + "".join(f"<td>{_md_inline(c)}</td>" for c in r)
                                 + "</tr>" for r in rows)
                       + "</tbody></table>")
            continue
        m = re.match(r"\s*([-*+]|\d+[.)])\s+(.*)", line)
        if m:
            flush()
            tag = "ol" if m.group(1)[0].isdigit() else "ul"
            if list_tag[0] != tag:
                close_list()
                out.append(f"<{tag}>")
                list_tag[0] = tag
            item = m.group(2)
            task = re.match(r"\[([ xX])\]\s+(.*)", item)
            if task:
                checked = " checked" if task.group(1) != " " else ""
                item_html = f'<input type="checkbox" disabled{checked}> {_md_inline(task.group(2))}'
            else:
                item_html = _md_inline(item)
            out.append(f"<li>{item_html}</li>")
            i += 1
            continue
        if list_tag[0] and line[:1] in (" ", "\t") and out and out[-1].endswith("</li>"):
            out[-1] = out[-1][:-5] + " " + _md_inline(stripped) + "</li>"
            i += 1
            continue
        close_list()
        para.append(stripped)
        i += 1
    flush()
    close_list()
    return "\n".join(out)


def markdown_to_html(text, title="Preview"):
    body = _md_blocks(text.replace("\r\n", "\n").split("\n"))
    return HTML_TEMPLATE.replace("__TITLE__", html.escape(title)).replace("__BODY__", body)


LANGUAGES.update({
    "yaml": _language(
        ("comment", r"(?:^|(?<=\s))#[^\n]*"),
        ("decorator", r"^---[ \t]*$|^\.\.\.[ \t]*$|[&*][\w-]+|![\w!/.-]*"),
        ("builtin", r"^[ \t]*(?:- )?[\w.\"'/ -]+?(?=:(?:[ \t]|$))"),
        ("string", STR_DQ + "|" + STR_SQ),
        ("keyword", _words("true false yes no on off null", ignore_case=True) + "|~"),
        ("number", r"(?<![\w.])-?\d+(?:\.\d+)?(?![\w.])"),
    ),
    "dockerfile": _language(
        ("comment", r"^[ \t]*#[^\n]*"),
        ("keyword", r"(?i:^[ \t]*(?:FROM|RUN|CMD|LABEL|MAINTAINER|EXPOSE|ENV|ADD|COPY|ENTRYPOINT|"
                    r"VOLUME|USER|WORKDIR|ARG|ONBUILD|STOPSIGNAL|HEALTHCHECK|SHELL)\b|\bAS\b)"),
        ("string", STR_DQ + "|" + STR_SQ),
        ("builtin", r"\$\{?\w+\}?"),
        ("decorator", r"--[\w-]+"),
        ("number", r"\b\d+\b"),
    ),
    "makefile": _language(
        ("comment", r"(?:^|(?<=[ \t]))#[^\n]*"),
        ("keyword", r"^[ \t]*(?:ifeq|ifneq|ifdef|ifndef|else|endif|include|define|endef|export|"
                    r"override)\b|\.PHONY"),
        ("decorator", r"^[\w.-]+(?=[ \t]*[:+?]?=)"),
        ("function", r"^[\w./%-]+(?=[ \t]*::?(?!=))"),
        ("builtin", r"\$\([^)\n]*\)|\$\{[^}\n]*\}|\$[@<^?*%]"),
        ("string", STR_DQ + "|" + STR_SQ),
    ),
    "powershell": _language(
        ("comment", r"<#[\s\S]*?(?:#>|\Z)|#[^\n]*"),
        ("string", r'@"[\s\S]*?(?:^"@|\Z)|' + r"@'[\s\S]*?(?:^'@|\Z)|" + STR_DQ + "|" + STR_SQ),
        ("builtin", r"\$\{[^}\n]*\}|\$[\w:]+"),
        ("keyword", _words("begin break catch class continue data do dynamicparam else elseif end "
                           "exit filter finally for foreach from function if in param process "
                           "return switch throw trap try until using var while workflow",
                           ignore_case=True)),
        ("function", r"\b[A-Za-z]+-[A-Za-z]+\b"),
        ("decorator", r"(?<![\w-])-[A-Za-z]+\b"),
        ("number", NUMBER),
    ),
    "ruby": _language(
        ("comment", r"^=begin[\s\S]*?(?:^=end|\Z)|#[^\n]*"),
        ("string", STR_DQ + "|" + STR_SQ + r"|%[qQwWi]?\{[^}]*\}?"),
        ("builtin", r"(?<![\w:]):[A-Za-z_]\w*[?!]?|@{1,2}\w+|\$\w+"),
        ("function", r"(?<=def )(?:self\.)?[\w?!=]+"),
        ("keyword", _words("BEGIN END alias and begin break case class def defined do else elsif "
                           "end ensure false for if in module next nil not or redo rescue retry "
                           "return self super then true undef unless until when while yield "
                           "require require_relative attr_accessor attr_reader attr_writer puts "
                           "private protected public lambda proc")),
        ("klass", r"\b[A-Z]\w*"),
        ("number", NUMBER),
    ),
    "lua": _language(
        ("comment", r"--\[\[[\s\S]*?(?:\]\]|\Z)|--[^\n]*"),
        ("string", STR_DQ + "|" + STR_SQ + r"|\[\[[\s\S]*?(?:\]\]|\Z)"),
        ("keyword", _words("and break do else elseif end false for function goto if in local nil "
                           "not or repeat return then true until while")),
        ("builtin", _words("print pairs ipairs type tostring tonumber require table string math os "
                           "io error pcall assert select setmetatable getmetatable unpack self")),
        ("function", r"(?<=function )[\w.:]+|\b\w+(?=\s*\()"),
        ("number", NUMBER),
    ),
    "log": _language(
        ("error", r"^.*\b(?:ERROR|ERR|FATAL|CRITICAL|CRIT|SEVERE|EXCEPTION|Exception|Traceback|"
                  r"FAIL|FAILED|FAILURE)\b.*$"),
        ("warning", r"^.*\b(?:WARN|WARNING)\b.*$"),
        ("comment", r"^.*\b(?:DEBUG|TRACE|VERBOSE)\b.*$"),
        ("number", r"\b\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:[.,]\d+)?(?:Z|[+-]\d{2}:?\d{2})?"
                   r"|\b\d{2}:\d{2}:\d{2}(?:[.,]\d+)?"),
        ("keyword", r"\bINFO\b|\bNOTICE\b"),
        ("string", STR_DQ),
        ("builtin", r"\bhttps?://\S+"),
    ),
    "http": _language(
        ("decorator", r"^###[^\n]*"),
        ("comment", r"^[ \t]*(?:#|//)[^\n]*"),
        ("keyword", r"^[ \t]*(?:GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS)\b"),
        ("function", r"^@\w+"),
        ("builtin", r"^[\w-]+(?=:[ \t])"),
        ("string", r"\bhttps?://\S+"),
        ("number", r"\{\{\w+\}\}"),
    ),
})
for _lang, _exts in (
        ("yaml", "yaml yml"), ("dockerfile", "dockerfile containerfile"),
        ("makefile", "makefile gnumakefile mk mak"), ("powershell", "ps1 psm1 psd1"),
        ("ruby", "rb rake gemspec ru"), ("lua", "lua"), ("log", "log out"),
        ("http", "http rest")):
    for _ext in _exts.split():
        EXTENSIONS[_ext] = _lang
AUTO_INDENT_OPENERS.update({"yaml": (":",), "powershell": ("{", "(", "["), "lua": ("then", "do"),
                            "ruby": ("do",)})
COMMENT_STYLES.update({"yaml": ("#", ""), "dockerfile": ("#", ""), "makefile": ("#", ""),
                       "powershell": ("#", ""), "ruby": ("#", ""), "lua": ("--", ""),
                       "log": ("#", ""), "http": ("#", "")})
LANG_NAMES = {
    "python": "Python", "clike": "JavaScript / Java / Go", "c": "C / C++ / C#", "json": "JSON",
    "markup": "HTML / XML", "css": "CSS", "ini": "INI / TOML", "sql": "SQL", "shell": "Shell",
    "batch": "Batch", "markdown": "Markdown", "yaml": "YAML", "dockerfile": "Dockerfile",
    "makefile": "Makefile", "powershell": "PowerShell", "ruby": "Ruby", "lua": "Lua", "log": "Log",
    "http": "HTTP Requests",
}
SWATCH_LANGS = {"css", "markup", "clike", "yaml", "ini", "markdown", "json"}
RUN_SELECTION_EXT = {"python": ".py", "shell": ".sh", "powershell": ".ps1", "clike": ".js",
                     "ruby": ".rb", "lua": ".lua", "batch": ".bat"}
DEFAULT_SNIPPETS = {
    "python": {
        "main": 'if __name__ == "__main__":\n    ${1:main()}$0',
        "def": "def ${1:name}(${2}):\n    ${0:pass}",
        "class": "class ${1:Name}:\n    def __init__(self${2}):\n        ${0:pass}",
        "for": "for ${1:item} in ${2:items}:\n    ${0:pass}",
        "while": "while ${1:condition}:\n    ${0:pass}",
        "if": "if ${1:condition}:\n    ${0:pass}",
        "try": "try:\n    ${1:pass}\nexcept ${2:Exception} as error:\n    ${0:print(error)}",
        "with": 'with open(${1:path}, encoding="utf-8") as ${2:f}:\n    ${0:data = f.read()}',
        "prop": "@property\ndef ${1:name}(self):\n    return self._${1:name}$0",
    },
    "clike": {
        "for": "for (let ${1:i} = 0; ${1:i} < ${2:count}; ${1:i}++) {\n    $0\n}",
        "if": "if (${1:condition}) {\n    $0\n}",
        "func": "function ${1:name}(${2}) {\n    $0\n}",
        "arrow": "const ${1:name} = (${2}) => {\n    $0\n};",
        "log": "console.log(${1});$0",
        "try": "try {\n    ${1}\n} catch (${2:error}) {\n    console.error(${2:error});\n}$0",
    },
    "c": {
        "for": "for (int ${1:i} = 0; ${1:i} < ${2:n}; ${1:i}++) {\n    $0\n}",
        "if": "if (${1:condition}) {\n    $0\n}",
        "main": "int main(void) {\n    $0\n    return 0;\n}",
        "inc": "#include <${1:stdio.h}>$0",
    },
    "markup": {
        "html": ('<!DOCTYPE html>\n<html lang="en">\n<head>\n    <meta charset="utf-8">\n'
                 '    <meta name="viewport" content="width=device-width, initial-scale=1">\n'
                 '    <title>${1:Title}</title>\n</head>\n<body>\n    $0\n</body>\n</html>'),
        "link": '<link rel="stylesheet" href="${1:style.css}">$0',
        "script": '<script src="${1:app.js}"></script>$0',
    },
    "css": {
        "media": "@media (max-width: ${1:600}px) {\n    $0\n}",
        "flex": "display: flex;\nalign-items: ${1:center};\njustify-content: ${2:center};$0",
        "grid": "display: grid;\ngrid-template-columns: ${1:repeat(3, 1fr)};\ngap: ${2:1rem};$0",
    },
    "markdown": {
        "table": "| ${1:Column 1} | ${2:Column 2} |\n|----------|----------|\n| $0 |  |",
        "link": "[${1:text}](${2:https://})$0",
        "code": "```${1}\n$0\n```",
        "img": "![${1:alt}](${2:image.png})$0",
        "task": "- [ ] ${1:task}$0",
    },
    "sql": {
        "sel": "SELECT ${1:*}\nFROM ${2:table}\nWHERE ${3:condition};$0",
        "ins": "INSERT INTO ${1:table} (${2:columns})\nVALUES (${3});$0",
        "upd": "UPDATE ${1:table}\nSET ${2:column} = ${3:value}\nWHERE ${4:condition};$0",
        "create": "CREATE TABLE ${1:name} (\n    id INTEGER PRIMARY KEY,\n    ${2:column} TEXT\n);$0",
    },
    "shell": {
        "if": "if [ ${1:condition} ]; then\n    $0\nfi",
        "for": "for ${1:item} in ${2:list}; do\n    $0\ndone",
        "bash": "#!/usr/bin/env bash\nset -euo pipefail\n\n$0",
        "func": "${1:name}() {\n    $0\n}",
    },
    "http": {
        "get": "### ${1:Request}\nGET ${2:https://httpbin.org/get}\nAccept: application/json\n$0",
        "post": ("### ${1:Request}\nPOST ${2:https://httpbin.org/post}\nContent-Type: application/json"
                 "\n\n{\n    \"${3:key}\": \"${4:value}\"\n}\n$0"),
    },
    "yaml": {
        "svc": "${1:name}:\n  image: ${2:image}\n  ports:\n    - \"${3:8080}:${4:80}\"$0",
    },
    "*": {
        "lorem": ("Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod "
                  "tempor incididunt ut labore et dolore magna aliqua.$0"),
        "date": "${1:YYYY-MM-DD}$0",
    },
}
TEMPLATES = {
    "Python Script": (".py", '#!/usr/bin/env python3\n\n\ndef main():\n    pass\n\n\n'
                             'if __name__ == "__main__":\n    main()\n'),
    "HTML Page": (".html", DEFAULT_SNIPPETS["markup"]["html"].replace("${1:Title}", "Title")
                  .replace("$0", "") + "\n"),
    "README (Markdown)": (".md", "# Project Name\n\nShort description.\n\n## Installation\n\n"
                                 "```\n\n```\n\n## Usage\n\n## License\n"),
    "JSON Document": (".json", '{\n    "name": "",\n    "version": "1.0.0"\n}\n'),
    "Shell Script": (".sh", "#!/usr/bin/env bash\nset -euo pipefail\n\n"),
    "CSS Stylesheet": (".css", "*,\n*::before,\n*::after {\n    box-sizing: border-box;\n}\n\n"
                               "body {\n    margin: 0;\n    font-family: system-ui, sans-serif;\n}\n"),
    "HTTP Requests": (".http", "@base = https://httpbin.org\n\n### Get example\nGET {{base}}/get\n"
                               "Accept: application/json\n\n### Post example\nPOST {{base}}/post\n"
                               "Content-Type: application/json\n\n{\n    \"hello\": \"world\"\n}\n"),
    "SQL Script": (".sql", "CREATE TABLE IF NOT EXISTS items (\n    id INTEGER PRIMARY KEY,\n"
                           "    name TEXT NOT NULL\n);\n\nINSERT INTO items (name) VALUES ('first');\n\n"
                           "SELECT * FROM items;\n"),
    "Plain Text": (".txt", ""),
}
DEFAULT_CONFIG.update({
    "show_minimap": False, "show_guides": True, "show_whitespace": False, "show_trailing": True,
    "mark_long": False, "show_ruler": False, "ruler_col": 80, "rainbow": True, "swatches": True,
    "typewriter": False, "focus_mode": False, "auto_save": False, "backup_bak": False,
    "detect_indent": True, "single_instance": True, "vim_mode": False, "explorer": False,
    "outline": False, "explorer_root": "", "ui_scale": "100", "word_goals": {},
})
VOID_TAGS = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta",
             "param", "source", "track", "wbr"}
KNOWN_TAGS = set("html head body div span p a ul ol li table tr td th thead tbody tfoot img "
                 "input button form label select option textarea h1 h2 h3 h4 h5 h6 header "
                 "footer nav main section article aside strong em code pre blockquote br hr "
                 "meta link script style title iframe video audio source canvas svg i b small "
                 "figure figcaption dl dt dd".split())
EMMET_ATTRS = {"a": [("href", "")], "img": [("src", ""), ("alt", "")],
               "link": [("rel", "stylesheet"), ("href", "")], "script": [("src", "")],
               "input": [("type", "text")], "form": [("action", "")], "label": [("for", "")],
               "meta": [("charset", "utf-8")], "iframe": [("src", "")]}
KEY_NAMES = {"plus": "+", "minus": "-", "equal": "=", "slash": "/", "backslash": "\\",
             "comma": ",", "period": ".", "grave": "`", "space": "Space", "Return": "Enter",
             "KP_Add": "Num +", "KP_Subtract": "Num -", "KP_Divide": "Num /",
             "bracketleft": "[", "bracketright": "]", "Prior": "PgUp", "Next": "PgDn",
             "ISO_Left_Tab": "Tab", "Escape": "Esc", "Delete": "Del", "BackSpace": "Backspace"}
MOD_NAMES = {"Control": "Ctrl", "Shift": "Shift", "Alt": "Alt", "Command": "Cmd",
             "Option": "Option", "Meta": "Meta"}
SPECIAL_CHARS = {
    "Arrows": "← → ↑ ↓ ↔ ↕ ⇐ ⇒ ⇑ ⇓ ⇔ ↩ ↪ ➜ ➔ ▲ ▼ ◀ ▶",
    "Math": "± × ÷ ≠ ≈ ≤ ≥ ∞ √ ∑ ∏ ∫ ∂ ∆ ∇ π µ ° ‰ ¹ ² ³ ½ ¼ ¾ ∈ ∉ ∩ ∪ ⊂ ⊃ ∧ ∨ ¬ ∀ ∃",
    "Currency": "€ £ ¥ ¢ ₹ ₽ ₩ ₿ ¤ $",
    "Punctuation": "– — … • · ¶ § † ‡ « » ‹ › “ ” ‘ ’ ¡ ¿ © ® ™ ℃ №",
    "Latin": "á é í ó ú ñ ü Á É Í Ó Ú Ñ Ü à è ì ò ù â ê î ô û ä ë ï ö ç ß ø å æ œ",
    "Greek": "α β γ δ ε ζ η θ ι κ λ μ ν ξ ο π ρ σ τ υ φ χ ψ ω Ω Σ Δ Φ Ψ Λ Γ Θ",
    "Box": "─ │ ┌ ┐ └ ┘ ├ ┤ ┬ ┴ ┼ ═ ║ ╔ ╗ ╚ ╝ ╠ ╣ ╦ ╩ ╬ █ ▓ ▒ ░ ■ □ ● ○ ◆ ◇ ★ ☆",
    "Symbols": "✓ ✔ ✗ ✘ ☐ ☑ ☒ ♠ ♣ ♥ ♦ ♪ ♫ ☀ ☁ ☂ ☎ ✉ ✂ ⚠ ⚡ ☺ ☹ ♻ ⌘ ⌥ ⇧ ⌫ ⏎",
}
FIRST_NAMES = ("Ana Luis Maria Carlos Sofia Jorge Elena Pedro Lucia Diego Laura Miguel Paula "
               "Javier Carmen Andres Valeria Daniel Isabel Ricardo Olivia Liam Emma Noah Ava "
               "James Mia Lucas Chloe Mateo").split()
LAST_NAMES = ("Garcia Martinez Lopez Hernandez Gonzalez Perez Sanchez Ramirez Torres Flores "
              "Rivera Gomez Diaz Cruz Morales Reyes Ortiz Smith Johnson Brown Miller Davis Wilson "
              "Moore Taylor Anderson Thomas Jackson White Harris").split()
CITIES = ("Mexico City, Guadalajara, Monterrey, Madrid, Barcelona, Bogota, Lima, Santiago, "
          "Buenos Aires, Phoenix, Los Angeles, New York, Chicago, Toronto, London").split(", ")
def blend(c1, c2, t):
    def rgb(c):
        c = c.lstrip("#")
        if len(c) == 3:
            c = "".join(ch * 2 for ch in c)
        return [int(c[i:i + 2], 16) for i in (0, 2, 4)]
    a, b = rgb(c1), rgb(c2)
    return "#" + "".join(f"{round(x + (y - x) * t):02X}" for x, y in zip(a, b))
def luminance(color):
    c = color.lstrip("#")
    if len(c) == 3:
        c = "".join(ch * 2 for ch in c)
    r, g, b = (int(c[i:i + 2], 16) / 255 for i in (0, 2, 4))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b
THEMES["High Contrast"] = {
    "bg": "#000000", "fg": "#FFFFFF", "sel_bg": "#FFFF00", "sel_fg": "#000000",
    "cursor": "#FFFF00", "gutter_bg": "#000000", "gutter_fg": "#FFFFFF",
    "status_bg": "#FFFF00", "status_fg": "#000000", "bracket": "#00A0A0",
    "curline": "#1A1A1A", "occur": "#004040", "bookmark": "#FFFF00",
    "diff_add": "#00FF00", "diff_del": "#FF4040", "diff_hunk": "#00FFFF",
    "comment": "#00FF00", "string": "#FFFF00", "number": "#FF80FF", "keyword": "#00FFFF",
    "builtin": "#80FFFF", "function": "#FFFFFF", "klass": "#FFFFFF", "decorator": "#FFA040",
    "operator": "#FFFFFF",
}
BASE_THEME = dict(THEMES["Dark"])
def complete_theme(theme):
    th = dict(BASE_THEME)
    th.update(theme)
    bg, fg = th["bg"], th["fg"]
    dark = luminance(bg) < 0.5
    defaults = {
        "error": th["diff_del"], "warning": th["bookmark"],
        "guide": blend(bg, fg, 0.10), "ws": blend(bg, fg, 0.07), "ws_tab": blend(bg, fg, 0.13),
        "trail": blend(bg, th["diff_del"], 0.45), "long": blend(bg, th["diff_del"], 0.15),
        "find_all": blend(bg, th["bookmark"], 0.35), "dim": blend(bg, fg, 0.35),
        "git_add": th["diff_add"], "git_mod": th["diff_hunk"], "git_del": th["diff_del"],
        "minimap_fg": blend(bg, fg, 0.35), "minimap_view": blend(bg, fg, 0.55),
        "ruler": blend(bg, fg, 0.22), "syntax_error": blend(bg, th["diff_del"], 0.35),
        "colsel": th["sel_bg"], "link": "#6CB6FF" if dark else "#0B66C3",
        "rainbow": (["#FFD700", "#DA70D6", "#179FFF"] if dark
                    else ["#0431FA", "#319331", "#7B3814"]),
        "code_bg": blend(bg, fg, 0.08),
        "side_bg": blend(bg, fg, 0.04) if dark else blend(bg, fg, 0.05),
        "side_fg": blend(fg, bg, 0.12),
        "side_header": blend(fg, bg, 0.35),
        "list_sel": blend(blend(bg, fg, 0.04), th["sel_bg"], 0.35 if dark else 0.45),
        "list_hover": blend(bg, fg, 0.10),
        "tabbar_bg": blend(bg, fg, 0.04) if dark else blend(bg, fg, 0.06),
        "tab_inactive_bg": blend(bg, fg, 0.08) if dark else blend(bg, fg, 0.10),
        "tab_inactive_fg": blend(fg, bg, 0.40),
        "tab_hover_bg": blend(bg, fg, 0.12),
        "border": blend(bg, fg, 0.16),
        "activity_bg": blend(bg, fg, 0.10) if dark else blend(bg, fg, 0.13),
        "activity_fg": blend(fg, bg, 0.45),
        "activity_active": fg,
        "accent": th["keyword"] if dark else "#005FB8",
        "scroll_thumb": blend(bg, fg, 0.22),
        "scroll_thumb_hover": blend(bg, fg, 0.35),
        "folder": "#DCB67A" if dark else "#C09553",
        "git_mod_fg": "#E2C08D" if dark else "#895503",
        "git_new_fg": "#73C991" if dark else "#388A34",
        "git_del_fg": "#C74E39" if dark else "#AD0707",
        "git_ign_fg": blend(fg, bg, 0.5),
    }
    for key, value in defaults.items():
        th.setdefault(key, value)
    if isinstance(th["rainbow"], str):
        th["rainbow"] = th["rainbow"].split()
    return th
def seq_to_accel(seq):
    parts = seq.strip("<>").split("-")
    mods = [MOD_NAMES.get(p, p) for p in parts[:-1] if p not in ("KeyPress", "Key")]
    key = KEY_NAMES.get(parts[-1], parts[-1])
    if len(key) == 1:
        key = key.upper()
    return "+".join(mods + [key])
def split_words(text):
    return re.findall(r"[A-Z]+(?=[A-Z][a-z])|[A-Z]?[a-z]+|[A-Z]+|\d+", text)
def convert_case(text, style):
    def convert(phrase):
        words = split_words(phrase)
        if not words:
            return phrase
        lower = [w.lower() for w in words]
        if style == "snake":
            return "_".join(lower)
        if style == "kebab":
            return "-".join(lower)
        if style == "constant":
            return "_".join(w.upper() for w in words)
        if style == "camel":
            return lower[0] + "".join(w.capitalize() for w in lower[1:])
        if style == "pascal":
            return "".join(w.capitalize() for w in lower)
        return phrase
    out = []
    for line in text.split("\n"):
        m = re.match(r"(\s*)(.*?)(\s*)$", line)
        out.append(m.group(1) + convert(m.group(2)) + m.group(3))
    return "\n".join(out)
def clean_invisible(text):
    text = re.sub("[​‌‍⁠﻿­]", "", text)
    return re.sub("[  -   　]", " ", text)
def straighten_quotes(text):
    table = {"“": '"', "”": '"', "„": '"', "‟": '"', "«": '"',
             "»": '"', "‘": "'", "’": "'", "‚": "'", "‛": "'",
             "′": "'", "″": '"', "…": "..."}
    return "".join(table.get(ch, ch) for ch in text)
def detect_indentation(text):
    tabs = spaces = 0
    deltas = {}
    prev = 0
    for line in text.split("\n")[:5000]:
        if not line.strip():
            continue
        lead = line[:len(line) - len(line.lstrip(" \t"))]
        if lead.startswith("\t"):
            tabs += 1
            continue
        n = len(lead)
        if n:
            spaces += 1
        delta = abs(n - prev)
        if delta in (2, 4, 8):
            deltas[delta] = deltas.get(delta, 0) + 1
        prev = n
    if tabs > spaces and tabs >= 3:
        return False, None
    if spaces >= 3 and deltas:
        width = max((4, 2, 8), key=lambda w: deltas.get(w, 0))
        if deltas.get(width):
            return True, width
    return None
def hex_lines(data, base):
    out = []
    for i in range(0, len(data), 16):
        chunk = data[i:i + 16]
        hx = " ".join(f"{b:02X}" for b in chunk)
        if len(chunk) > 8:
            hx = hx[:23] + " " + hx[24:]
        text = "".join(chr(b) if 32 <= b < 127 else "." for b in chunk)
        out.append(f"{base + i:08X}  {hx:<48}  |{text}|")
    return out
def format_bytes(n):
    for unit in ("bytes", "KB", "MB", "GB"):
        if n < 1024 or unit == "GB":
            return f"{n:,} {unit}" if unit == "bytes" else f"{n:.1f} {unit}"
        n /= 1024
    return str(n)
def md_slug(title):
    slug = re.sub(r"[^\w\- ]", "", title.lower()).strip()
    return re.sub(r"\s+", "-", slug)
def markdown_toc(text):
    lines = []
    in_code = False
    for line in text.split("\n"):
        if line.strip().startswith(("```", "~~~")):
            in_code = not in_code
            continue
        m = None if in_code else re.match(r"(#{1,6})\s+(.*?)\s*#*\s*$", line)
        if m:
            level = len(m.group(1))
            title = m.group(2)
            lines.append("  " * (level - 1) + f"- [{title}](#{md_slug(title)})")
    return "\n".join(lines)
def _emmet_parse(abbr):
    pos = 0
    n = len(abbr)

    def ident():
        nonlocal pos
        m = re.compile(r"[\w$:@-]+").match(abbr, pos)
        if not m:
            raise ValueError("identifier expected")
        pos = m.end()
        return m.group()

    def count():
        nonlocal pos
        if pos < n and abbr[pos] == "*":
            pos += 1
            m = re.compile(r"\d+").match(abbr, pos)
            if not m:
                raise ValueError("number expected")
            pos = m.end()
            return max(1, min(100, int(m.group())))
        return 1

    def element():
        nonlocal pos
        node = {"tag": None, "id": None, "classes": [], "attrs": [], "text": None, "children": []}
        m = re.compile(r"[A-Za-z][\w:-]*").match(abbr, pos)
        if m:
            node["tag"] = m.group()
            pos = m.end()
        consumed = bool(m)
        while pos < n and abbr[pos] in "#.[{":
            ch = abbr[pos]
            pos += 1
            consumed = True
            if ch == "#":
                node["id"] = ident()
            elif ch == ".":
                node["classes"].append(ident())
            elif ch == "[":
                end = abbr.find("]", pos)
                if end < 0:
                    raise ValueError("] expected")
                for am in re.finditer(r'([\w:-]+)(?:=(?:"([^"]*)"|\'([^\']*)\'|([^\s\]]*)))?',
                                      abbr[pos:end]):
                    value = am.group(2) or am.group(3) or am.group(4) or ""
                    node["attrs"].append((am.group(1), value))
                pos = end + 1
            else:
                end = abbr.find("}", pos)
                if end < 0:
                    raise ValueError("} expected")
                node["text"] = abbr[pos:end]
                pos = end + 1
        if not consumed:
            raise ValueError("element expected")
        if node["tag"] is None:
            node["tag"] = "div"
        return node

    def expr():
        nonlocal pos
        root = {"children": []}
        parents = [root]
        last = None
        while pos < n:
            ch = abbr[pos]
            if ch == ")":
                break
            if ch == ">":
                if last is None:
                    raise ValueError("> without element")
                parents.append(last["group"][-1] if "group" in last else last)
                pos += 1
                last = None
                continue
            if ch == "+":
                pos += 1
                last = None
                continue
            if ch == "^":
                pos += 1
                if len(parents) > 1:
                    parents.pop()
                last = None
                continue
            if ch == "(":
                pos += 1
                group = expr()
                if pos >= n or abbr[pos] != ")":
                    raise ValueError(") expected")
                pos += 1
                node = {"group": group, "repeat": count()}
            else:
                node = element()
                node["repeat"] = count()
            parents[-1]["children"].append(node)
            last = node
        return root["children"]

    result = expr()
    if pos != n:
        raise ValueError("unexpected character")
    return result
def emmet_expand(abbr, unit):
    if not re.fullmatch(r"[\w.#>+*^()\[\]{}=\"'$:@ -]+", abbr) or abbr[0] in ">+^*":
        return None
    if not (set(abbr) & set(">+*.#[{(^")) and abbr not in KNOWN_TAGS:
        return None
    try:
        nodes = _emmet_parse(abbr)
    except ValueError:
        return None
    marker = "\x00"

    def number(text, i):
        return re.sub(r"\$+", lambda m: str(i).zfill(len(m.group())), text)

    def render(items, depth, out):
        for node in items:
            for i in range(1, node["repeat"] + 1):
                if "group" in node:
                    render(node["group"], depth, out)
                    continue
                tag = node["tag"]
                attrs = []
                if node["id"]:
                    attrs.append(("id", number(node["id"], i)))
                if node["classes"]:
                    attrs.append(("class", " ".join(number(c, i) for c in node["classes"])))
                given = [(k, number(v, i)) for k, v in node["attrs"]]
                attrs.extend(given)
                names = {k for k, _ in attrs}
                for k, v in EMMET_ATTRS.get(tag, []):
                    if k not in names:
                        attrs.append((k, v))
                attr_text = "".join(f' {k}="{v if v else marker}"' for k, v in attrs)
                pad = unit * depth
                text = number(node["text"], i) if node["text"] is not None else ""
                if tag in VOID_TAGS:
                    out.append(f"{pad}<{tag}{attr_text}>")
                elif node["children"]:
                    out.append(f"{pad}<{tag}{attr_text}>{text}")
                    render(node["children"], depth + 1, out)
                    out.append(f"{pad}</{tag}>")
                else:
                    out.append(f"{pad}<{tag}{attr_text}>{text or marker}</{tag}>")

    lines = []
    render(nodes, 0, lines)
    result = "\n".join(lines)
    cursor = result.find(marker)
    result = result.replace(marker, "")
    return result, (cursor if cursor >= 0 else len(result))
def pdf_escape(text):
    data = text.encode("cp1252", errors="replace")
    return data.replace(b"\\", b"\\\\").replace(b"(", b"\\(").replace(b")", b"\\)")
def build_pdf(text, title, numbers=True, header=True, width=612, height=792, margin=40,
              font_size=9, leading=11):
    cols = int((width - 2 * margin) / (font_size * 0.6))
    rows = int((height - 2 * margin) / leading) - (2 if header else 0)
    source = text.split("\n")
    digits = len(str(len(source)))
    wrapped = []
    for n, line in enumerate(source, 1):
        line = line.expandtabs(4)
        prefix = f"{n:>{digits}}  " if numbers else ""
        avail = max(10, cols - len(prefix))
        chunks = [line[i:i + avail] for i in range(0, len(line), avail)] or [""]
        for k, chunk in enumerate(chunks):
            wrapped.append((prefix if k == 0 else " " * len(prefix)) + chunk)
    pages = [wrapped[i:i + rows] for i in range(0, len(wrapped), rows)] or [[]]
    stamp = time.strftime("%Y-%m-%d %H:%M")
    objects = []

    def add(data):
        objects.append(data)
        return len(objects)

    catalog = add(b"")
    pages_id = add(b"")
    font = add(b"<< /Type /Font /Subtype /Type1 /BaseFont /Courier /Encoding /WinAnsiEncoding >>")
    kids = []
    for number, lines in enumerate(pages, 1):
        ops = [f"BT /F1 {font_size} Tf {leading} TL {margin} {height - margin} Td".encode()]
        if header:
            head = f"{title}    Page {number} of {len(pages)}    {stamp}"
            ops.append(b"(" + pdf_escape(head[:cols]) + b") Tj T* T*")
        for line in lines:
            ops.append(b"(" + pdf_escape(line) + b") Tj T*")
        ops.append(b"ET")
        stream = b"\n".join(ops)
        content = add(b"<< /Length %d >>\nstream\n" % len(stream) + stream + b"\nendstream")
        kids.append(add((f"<< /Type /Page /Parent {pages_id} 0 R /MediaBox [0 0 {width} {height}] "
                         f"/Resources << /Font << /F1 {font} 0 R >> >> /Contents {content} 0 R >>")
                        .encode()))
    objects[catalog - 1] = f"<< /Type /Catalog /Pages {pages_id} 0 R >>".encode()
    objects[pages_id - 1] = (f"<< /Type /Pages /Kids [{' '.join(f'{k} 0 R' for k in kids)}] "
                             f"/Count {len(kids)} >>").encode()
    out = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = []
    for i, obj in enumerate(objects, 1):
        offsets.append(len(out))
        out += b"%d 0 obj\n" % i + obj + b"\nendobj\n"
    xref = len(out)
    out += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objects) + 1)
    for off in offsets:
        out += b"%010d 00000 n \n" % off
    out += b"trailer\n<< /Size %d /Root %d 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (
        len(objects) + 1, catalog, xref)
    return bytes(out)
def export_html(content, lang, theme, title, numbers=False):
    spans = []
    if lang in LANGUAGES and len(content) <= HIGHLIGHT_LIMIT:
        for m in LANGUAGES[lang].finditer(content):
            if m.end() > m.start():
                spans.append((m.start(), m.end(), theme[m.lastgroup.rsplit("_", 1)[0]]))
    parts = []
    pos = 0
    for start, end, color in spans:
        if start < pos:
            continue
        parts.append(html.escape(content[pos:start], quote=False))
        parts.append(f'<span style="color:{color}">{html.escape(content[start:end], quote=False)}'
                     f'</span>')
        pos = end
    parts.append(html.escape(content[pos:], quote=False))
    body = "".join(parts)
    if numbers:
        lines = body.split("\n")
        digits = len(str(len(lines)))
        body = "\n".join(f'<span style="color:{theme["gutter_fg"]};user-select:none">'
                         f'{i:>{digits}}  </span>{line}' for i, line in enumerate(lines, 1))
    return (f"<!DOCTYPE html>\n<html><head><meta charset=\"utf-8\"><title>{html.escape(title)}"
            f"</title></head>\n<body style=\"margin:0;background:{theme['bg']}\">\n"
            f"<pre style=\"margin:0;padding:16px;background:{theme['bg']};color:{theme['fg']};"
            f"font-family:Consolas,Menlo,'DejaVu Sans Mono',monospace;font-size:14px;"
            f"line-height:1.45;tab-size:4\">{body}</pre>\n</body></html>\n")
def generate_test_data(rows, fmt):
    rng = random.Random()
    records = []
    for i in range(1, rows + 1):
        first, last = rng.choice(FIRST_NAMES), rng.choice(LAST_NAMES)
        records.append({
            "id": i, "first_name": first, "last_name": last,
            "email": f"{first.lower()}.{last.lower()}{rng.randint(1, 99)}@example.com",
            "city": rng.choice(CITIES),
            "birth_date": (datetime.date(1960, 1, 1)
                           + datetime.timedelta(days=rng.randint(0, 16000))).isoformat(),
            "amount": round(rng.uniform(10, 5000), 2), "active": rng.random() > 0.3,
        })
    if fmt == "JSON":
        return json.dumps(records, indent=4, ensure_ascii=False)
    if fmt == "SQL":
        cols = list(records[0]) if records else []
        lines = []
        for r in records:
            values = ", ".join(str(int(v)) if isinstance(v, bool) else
                               (str(v) if isinstance(v, (int, float)) else
                                "'" + str(v).replace("'", "''") + "'") for v in r.values())
            lines.append(f"INSERT INTO people ({', '.join(cols)}) VALUES ({values});")
        return "\n".join(lines)
    buf = io.StringIO()
    if records:
        writer = csv.DictWriter(buf, fieldnames=list(records[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(records)
    return buf.getvalue().rstrip("\n")
def parse_http_blocks(text):
    lines = text.split("\n")
    variables = {}
    for line in lines:
        m = re.match(r"^@(\w+)\s*=\s*(.*?)\s*$", line)
        if m:
            variables[m.group(1)] = m.group(2)
    blocks = []
    start = 0
    for i, line in enumerate(lines + ["###"]):
        if line.startswith("###"):
            if i > start:
                blocks.append((start, i - 1))
            start = i
    return lines, blocks, variables
def parse_http_request(lines, variables):
    def sub(s):
        return re.sub(r"\{\{(\w+)\}\}", lambda m: variables.get(m.group(1), m.group(0)), s)

    rows = [l for l in lines if not l.startswith("###") and not re.match(r"^\s*(#|//)", l)
            and not re.match(r"^@\w+\s*=", l)]
    while rows and not rows[0].strip():
        rows.pop(0)
    if not rows:
        return None
    first = sub(rows[0].strip())
    m = re.match(r"^(GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS)\s+(\S+)(?:\s+HTTP/[\d.]+)?$",
                 first, re.IGNORECASE)
    if m:
        method, url = m.group(1).upper(), m.group(2)
    elif re.match(r"^https?://", first):
        method, url = "GET", first.split()[0]
    else:
        return None
    headers = {}
    i = 1
    while i < len(rows) and rows[i].strip():
        hm = re.match(r"^([\w-]+)\s*:\s*(.*)$", rows[i])
        if hm:
            headers[hm.group(1)] = sub(hm.group(2))
        i += 1
    body = sub("\n".join(rows[i + 1:]).strip("\n")) if i < len(rows) else ""
    return method, url, headers, body
def git_run(args, cwd):
    if not cwd or not os.path.isdir(cwd) or not shutil.which("git"):
        return None
    try:
        result = subprocess.run(["git"] + args, cwd=cwd, capture_output=True, timeout=3,
                                creationflags=NO_WINDOW)
    except (OSError, subprocess.SubprocessError):
        return None
    return result.stdout if result.returncode == 0 else None
def reveal_in_file_manager(path):
    folder = path if os.path.isdir(path) else os.path.dirname(path)
    if sys.platform == "win32":
        if os.path.isfile(path):
            subprocess.Popen(f'explorer /select,"{os.path.normpath(path)}"')
        else:
            os.startfile(folder)
    elif sys.platform == "darwin":
        subprocess.Popen(["open", "-R", path] if os.path.isfile(path) else ["open", folder])
    else:
        subprocess.Popen(["xdg-open", folder])
def os_dark_mode():
    try:
        if sys.platform == "win32":
            import winreg
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path) as key:
                return winreg.QueryValueEx(key, "AppsUseLightTheme")[0] == 0
        if sys.platform == "darwin":
            result = subprocess.run(["defaults", "read", "-g", "AppleInterfaceStyle"],
                                    capture_output=True, text=True, timeout=2)
            return "dark" in result.stdout.lower()
        if shutil.which("gsettings"):
            for key in ("color-scheme", "gtk-theme"):
                result = subprocess.run(["gsettings", "get", "org.gnome.desktop.interface", key],
                                        capture_output=True, text=True, timeout=2)
                if "dark" in result.stdout.lower():
                    return True
        return "dark" in os.environ.get("GTK_THEME", "").lower()
    except (OSError, subprocess.SubprocessError, ImportError):
        return False
def load_json_file(path, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return default
def write_json_file(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
def path_key(path):
    return hashlib.sha1(os.path.normcase(os.path.abspath(path)).encode("utf-8")).hexdigest()[:16]
def md_inline_insert(widget, text, base_tags, links):
    pattern = re.compile(r"(\*\*.+?\*\*|__.+?__|(?<![\w*])\*(?!\s).+?(?<!\s)\*(?![\w*])|"
                         r"(?<![\w_])_(?!\s).+?(?<!\s)_(?![\w_])|`[^`]+`|~~.+?~~|"
                         r"!?\[[^\]]*\]\([^)\s]*\))")
    pos = 0
    for m in pattern.finditer(text):
        if m.start() > pos:
            widget.insert("end", text[pos:m.start()], base_tags)
        token = m.group()
        if token.startswith(("**", "__")):
            widget.insert("end", token[2:-2], base_tags + ("md_b",))
        elif token.startswith("~~"):
            widget.insert("end", token[2:-2], base_tags + ("md_s",))
        elif token.startswith("`"):
            widget.insert("end", token[1:-1], base_tags + ("md_icode",))
        elif token.startswith(("[", "![")):
            lm = re.match(r"(!?)\[([^\]]*)\]\(([^)\s]*)\)", token)
            if lm.group(1):
                widget.insert("end", f"[image: {lm.group(2) or lm.group(3)}]", base_tags + ("md_i",))
            else:
                tag = f"md_link{len(links)}"
                links.append((tag, lm.group(3)))
                widget.insert("end", lm.group(2) or lm.group(3), base_tags + ("md_link", tag))
        else:
            widget.insert("end", token[1:-1], base_tags + ("md_i",))
        pos = m.end()
    if pos < len(text):
        widget.insert("end", text[pos:], base_tags)
def md_render(widget, text):
    links = []
    widget.config(state="normal")
    widget.delete("1.0", "end")
    in_code = False
    for line in text.replace("\r\n", "\n").split("\n"):
        s = line.strip()
        if s.startswith(("```", "~~~")):
            in_code = not in_code
            continue
        if in_code:
            widget.insert("end", line + "\n", ("md_code",))
            continue
        m = re.match(r"(#{1,6})\s+(.*?)\s*#*\s*$", s)
        if m:
            md_inline_insert(widget, m.group(2), (f"md_h{min(len(m.group(1)), 4)}",), links)
            widget.insert("end", "\n")
            continue
        if re.fullmatch(r"([-*_])(\s*\1){2,}", s):
            widget.insert("end", "─" * 40 + "\n", ("md_hr",))
            continue
        if s.startswith(">"):
            md_inline_insert(widget, re.sub(r"^(>\s?)+", "", s), ("md_quote",), links)
            widget.insert("end", "\n")
            continue
        if re.fullmatch(r"\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)*\|?", s):
            continue
        if s.startswith("|") and s.count("|") >= 2:
            widget.insert("end", " │ ".join(_md_cells(s)) + "\n", ("md_table",))
            continue
        m = re.match(r"(\s*)([-*+]|\d+[.)])\s+(.*)", line)
        if m:
            depth = len(m.group(1).expandtabs(4)) // 2
            bullet = m.group(2) if m.group(2)[0].isdigit() else "•"
            item = m.group(3)
            task = re.match(r"\[([ xX])\]\s+(.*)", item)
            if task:
                bullet = "☑" if task.group(1) != " " else "☐"
                item = task.group(2)
            widget.insert("end", "    " * depth + bullet + " ", ("md_li",))
            md_inline_insert(widget, item, ("md_li",), links)
            widget.insert("end", "\n")
            continue
        if not s:
            widget.insert("end", "\n")
            continue
        md_inline_insert(widget, s, (), links)
        widget.insert("end", "\n")
    widget.config(state="disabled")
    return links
def python_symbols(content):
    tree = ast.parse(content)
    out = []

    def visit(nodes, depth, prefix):
        for node in nodes:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                kind = "class" if isinstance(node, ast.ClassDef) else "def"
                out.append({"name": node.name, "line": node.lineno, "depth": depth, "kind": kind,
                            "full": prefix + node.name, "node": node})
                visit(node.body, depth + 1, prefix + node.name + ".")
    visit(tree.body, 0, "")
    return out
SYMBOL_PATTERNS = {
    "clike": r"^[ \t]*(?:export\s+)?(?:default\s+)?(?:async\s+)?(?:function\*?\s+(\w+)|class\s+(\w+)"
             r"|(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s*)?(?:function|\([^)]*\)\s*=>|\w+\s*=>)"
             r"|(?:public|private|protected|static|func|fn|def)\s+[\w<>\[\], ]*?(\w+)\s*\()",
    "c": r"^[ \t]*(?:class|struct|enum|namespace)\s+(\w+)|^[ \t]*[\w:<>\*&]+[ \t\*&]+(\w+)\s*\([^;]*$",
    "css": r"^[ \t]*([^{}\n/][^{}\n]*?)\s*\{",
    "ini": r"^[ \t]*\[([^\]\n]+)\]",
    "sql": r"(?i:^[ \t]*create\s+(?:or\s+replace\s+)?(?:table|view|index|function|procedure|"
           r"trigger)\s+(?:if\s+not\s+exists\s+)?([\w.\"`\[\]]+))",
    "shell": r"^[ \t]*(?:function\s+)?(\w+)\s*\(\)",
    "batch": r"^[ \t]*:(\w+)",
    "yaml": r"^([\w.\"'-][^:\n#]*):",
    "ruby": r"^[ \t]*(?:def|class|module)\s+((?:self\.)?[\w?!=:]+)",
    "lua": r"^[ \t]*(?:local\s+)?function\s+([\w.:]+)",
    "powershell": r"(?i:^[ \t]*function\s+([\w-]+))",
    "makefile": r"^([\w./%-]+)\s*::?(?!=)",
    "dockerfile": r"(?i:^[ \t]*FROM\s+\S+\s+AS\s+(\w+))",
    "http": r"^###[ \t]*(.+)$",
}
def find_symbols(content, lang):
    if lang == "python":
        try:
            return [{k: v for k, v in s.items() if k != "node"} for s in python_symbols(content)]
        except (SyntaxError, ValueError):
            pass
    out = []
    if lang == "markdown":
        in_code = False
        for n, line in enumerate(content.split("\n"), 1):
            if line.strip().startswith(("```", "~~~")):
                in_code = not in_code
                continue
            m = None if in_code else re.match(r"(#{1,6})\s+(.*?)\s*#*\s*$", line)
            if m:
                out.append({"name": m.group(2), "line": n, "depth": len(m.group(1)) - 1,
                            "kind": "heading", "full": m.group(2)})
        return out
    pattern = SYMBOL_PATTERNS.get(lang)
    if lang == "python":
        pattern = r"^[ \t]*(?:async\s+)?(?:def|class)\s+(\w+)"
    if not pattern:
        return out
    regex = re.compile(pattern, re.MULTILINE)
    index = make_indexer(content)
    for m in regex.finditer(content):
        name = next((g for g in m.groups() if g), None)
        if not name:
            continue
        line = int(index(m.start()).split(".")[0])
        lead = content[m.start():].split("\n", 1)[0]
        depth = (len(lead) - len(lead.lstrip())) // 4
        out.append({"name": name.strip(), "line": line, "depth": depth, "kind": "symbol",
                    "full": name.strip()})
    return out
FILE_COLORS = {
    "py": "#3572A5", "pyw": "#3572A5", "ipynb": "#DA5B0B", "js": "#E5C33B", "mjs": "#E5C33B",
    "cjs": "#E5C33B", "jsx": "#61DAFB", "ts": "#3178C6", "tsx": "#3178C6", "json": "#CBCB41",
    "html": "#E34C26", "htm": "#E34C26", "css": "#663399", "scss": "#C6538C", "less": "#1D365D",
    "md": "#519ABA", "markdown": "#519ABA", "txt": "#9DA5B4", "log": "#9DA5B4", "csv": "#89E051",
    "tsv": "#89E051", "sql": "#E38C00", "db": "#E38C00", "sqlite": "#E38C00", "sh": "#89E051",
    "bash": "#89E051", "zsh": "#89E051", "ps1": "#5391FE", "bat": "#C1F12E", "cmd": "#C1F12E",
    "yml": "#CB171E", "yaml": "#CB171E", "toml": "#9C4221", "ini": "#D4A72C", "cfg": "#D4A72C",
    "conf": "#D4A72C", "env": "#ECD53F", "xml": "#0060AC", "svg": "#FFB13B", "png": "#A074C4",
    "jpg": "#A074C4", "jpeg": "#A074C4", "gif": "#A074C4", "ico": "#A074C4", "webp": "#A074C4",
    "bmp": "#A074C4", "zip": "#E8B04B", "gz": "#E8B04B", "tar": "#E8B04B", "7z": "#E8B04B",
    "rar": "#E8B04B", "pdf": "#E44D26", "doc": "#2B579A", "docx": "#2B579A", "xls": "#217346",
    "xlsx": "#217346", "c": "#A8B9CC", "h": "#A8B9CC", "cpp": "#F34B7D", "hpp": "#F34B7D",
    "cs": "#178600", "java": "#B07219", "kt": "#A97BFF", "go": "#00ADD8", "rs": "#DEA584",
    "rb": "#CC342D", "php": "#4F5D95", "lua": "#5C7CFA", "swift": "#F05138", "dart": "#00B4AB",
    "r": "#198CE7", "http": "#E37933", "rest": "#E37933", "lock": "#9DA5B4", "exe": "#9DA5B4",
    "dockerfile": "#2496ED", "makefile": "#6D8086", "gitignore": "#F14E32", "license": "#D0BF41",
    "readme": "#519ABA",
}
def file_color(name):
    lower = name.lower()
    base = lower.split(".")[0]
    if base in FILE_COLORS and "." not in lower.strip("."):
        return FILE_COLORS[base]
    if lower.startswith("dockerfile"):
        return FILE_COLORS["dockerfile"]
    if lower in ("makefile", "gnumakefile"):
        return FILE_COLORS["makefile"]
    if base in ("readme", "license"):
        return FILE_COLORS[base]
    return FILE_COLORS.get(os.path.splitext(lower)[1].lstrip(".") or lower.lstrip("."), "#9DA5B4")
def _seg_dist(px, py, x1, y1, x2, y2):
    dx, dy = x2 - x1, y2 - y1
    length = dx * dx + dy * dy
    t = 0.0 if length == 0 else max(0.0, min(1.0, ((px - x1) * dx + (py - y1) * dy) / length))
    cx, cy = x1 + t * dx, y1 + t * dy
    return math.hypot(px - cx, py - cy)
def _in_poly(px, py, pts):
    inside = False
    j = len(pts) - 1
    for i in range(len(pts)):
        xi, yi = pts[i]
        xj, yj = pts[j]
        if (yi > py) != (yj > py) and px < (xj - xi) * (py - yi) / ((yj - yi) or 1e-9) + xi:
            inside = not inside
        j = i
    return inside
def _shape_hit(shape, x, y):
    kind = shape[0]
    if kind == "line":
        _, x1, y1, x2, y2, w = shape
        return _seg_dist(x, y, x1, y1, x2, y2) <= w / 2
    if kind == "poly":
        return _in_poly(x, y, shape[1])
    if kind == "stroke":
        pts, w, closed = shape[1], shape[2], shape[3]
        segs = list(zip(pts, pts[1:] + (pts[:1] if closed else [])))
        return any(_seg_dist(x, y, a[0], a[1], b[0], b[1]) <= w / 2 for a, b in segs)
    if kind == "circle":
        _, cx, cy, r, w = shape
        d = math.hypot(x - cx, y - cy)
        return d <= r if w == 0 else abs(d - r) <= w / 2
    if kind == "arc":
        _, cx, cy, r, w, a1, a2 = shape
        d = math.hypot(x - cx, y - cy)
        angle = math.degrees(math.atan2(cy - y, x - cx)) % 360
        inside = a1 <= angle <= a2 if a1 <= a2 else (angle >= a1 or angle <= a2)
        return abs(d - r) <= w / 2 and inside
    if kind == "gear":
        _, cx, cy = shape
        d = math.hypot(x - cx, y - cy)
        angle = math.atan2(y - cy, x - cx)
        if 3.2 <= d <= 7.2:
            return True
        return 7.2 < d <= 9.6 and math.cos(8 * angle) > 0.15
    return False
_ICON_CACHE = {}
def draw_icon(master, size, layers, bg):
    key = (str(master.tk), size, repr(layers), bg)
    if key in _ICON_CACHE:
        return _ICON_CACHE[key]
    img = tk.PhotoImage(master=master, width=size, height=size)
    offsets = [(i + 0.5) / 3 for i in range(3)]
    for y in range(size):
        row = []
        for x in range(size):
            color = None
            best = 0
            for shapes, fg in layers:
                hits = sum(1 for oy in offsets for ox in offsets
                           if any(_shape_hit(s, x + ox, y + oy) for s in shapes))
                if hits:
                    color = blend(color or bg, fg, hits / 9) if hits < 9 else fg
                    best = max(best, hits)
            row.append(color)
        for x, color in enumerate(row):
            if color:
                img.put(color, to=(x, y, x + 1, y + 1))
    _ICON_CACHE[key] = img
    return img
def file_icon_layers(name):
    color = file_color(name)
    page = [(3.5, 1.5), (9.5, 1.5), (12.5, 4.5), (12.5, 14.5), (3.5, 14.5)]
    fold = [(9.5, 1.5), (9.5, 4.5), (12.5, 4.5)]
    return [([("poly", page)], color), ([("poly", fold)], blend(color, "#FFFFFF", 0.5))]
def folder_icon_layers(color, opened=False, up=False):
    back = [(1.5, 3.0), (6.0, 3.0), (7.5, 4.5), (14.5, 4.5), (14.5, 13.5), (1.5, 13.5)]
    layers = [([("poly", back)], blend(color, "#000000", 0.25) if opened else color)]
    if opened:
        layers.append(([("poly", [(3.0, 7.0), (15.5, 7.0), (13.5, 13.5), (1.5, 13.5)])], color))
    if up:
        layers.append(([("line", 8, 12, 8, 6.5, 1.6), ("line", 5.5, 9, 8, 6.3, 1.6),
                        ("line", 10.5, 9, 8, 6.3, 1.6)], "#FFFFFF"))
    return layers
ICON_SHAPES = {
    "files": [("stroke", [(5, 7), (13, 7), (17, 11), (17, 21), (5, 21)], 1.6, True),
              ("stroke", [(8, 7), (8, 3), (16, 3), (20, 7), (20, 18), (17, 18)], 1.6, False)],
    "search": [("circle", 10.5, 10.5, 6, 1.8), ("line", 15, 15, 20.5, 20.5, 2.2)],
    "outline": [("line", 9, 7, 20, 7, 1.8), ("line", 9, 12, 20, 12, 1.8),
                ("line", 9, 17, 20, 17, 1.8), ("circle", 5, 7, 1.5, 0),
                ("circle", 5, 12, 1.5, 0), ("circle", 5, 17, 1.5, 0)],
    "run": [("stroke", [(7, 5), (19, 12), (7, 19)], 1.8, True)],
    "settings": [("gear", 12, 12)],
    "new_file": [("stroke", [(3.5, 2.5), (8.5, 2.5), (11.5, 5.5), (11.5, 13.5), (3.5, 13.5)],
                  1.1, True), ("line", 12, 9.5, 12, 15, 1.3), ("line", 9.3, 12.3, 14.7, 12.3, 1.3)],
    "new_folder": [("stroke", [(1.5, 3.5), (5.5, 3.5), (7, 5), (13.5, 5), (13.5, 8.5)], 1.1, False),
                   ("stroke", [(1.5, 3.5), (1.5, 13), (8.5, 13)], 1.1, False),
                   ("line", 12, 9.5, 12, 15, 1.3), ("line", 9.3, 12.3, 14.7, 12.3, 1.3)],
    "refresh": [("arc", 8, 8, 5, 1.4, 70, 350), ("poly", [(7.0, 0.8), (11.6, 3.0), (7.4, 5.8)])],
    "collapse": [("stroke", [(3, 5), (3, 13), (11, 13)], 1.1, False),
                 ("stroke", [(5.5, 2.5), (13.5, 2.5), (13.5, 10.5), (5.5, 10.5)], 1.1, True),
                 ("line", 7.5, 6.5, 11.5, 6.5, 1.2)],
    "up": [("line", 8, 13.5, 8, 3, 1.4), ("line", 3.8, 7.2, 8, 3, 1.4),
           ("line", 12.2, 7.2, 8, 3, 1.4)],
    "close": [("line", 4, 4, 12, 12, 1.3), ("line", 12, 4, 4, 12, 1.3)],
    "expand_all": [("stroke", [(2.5, 2.5), (13.5, 2.5), (13.5, 13.5), (2.5, 13.5)], 1.1, True),
                   ("line", 5, 8, 11, 8, 1.2), ("line", 8, 5, 8, 11, 1.2)],
}
SYMBOL_COLORS = {"class": "#EE9D28", "def": "#B180D7", "heading": "#519ABA", "symbol": "#75BEFF"}
def symbol_icon_layers(kind):
    color = SYMBOL_COLORS.get(kind, "#75BEFF")
    if kind == "class":
        return [([("poly", [(8, 2), (14, 8), (8, 14), (2, 8)])], color)]
    if kind == "heading":
        return [([("line", 5.5, 3, 4.5, 13, 1.3), ("line", 10.5, 3, 9.5, 13, 1.3),
                  ("line", 3, 6, 13, 6, 1.3), ("line", 2.5, 10, 12.5, 10, 1.3)], color)]
    return [([("poly", [(8, 2), (13.5, 5), (13.5, 11), (8, 14), (2.5, 11), (2.5, 5)])], color)]


class _ProxyMixin:

    def _install_proxy(self):
        self.on_change = None
        self.on_cursor = None
        self._orig = self._w + "_orig"
        self.tk.call("rename", self._w, self._orig)
        self.tk.createcommand(self._w, self._proxy)

    def _proxy(self, *args):
        try:
            result = self.tk.call((self._orig,) + args)
        except tk.TclError:
            return ""
        cmd = args[0] if args else ""
        changed = cmd in ("insert", "delete", "replace") or (
            cmd == "edit" and len(args) > 1 and args[1] in ("undo", "redo"))
        moved = changed or (cmd == "mark" and len(args) > 2
                            and args[1] == "set" and args[2] == "insert")
        if changed and self.on_change:
            self.on_change()
        if moved and self.on_cursor:
            self.on_cursor()
        return result

    def destroy(self):
        super().destroy()
        try:
            self.tk.deletecommand(self._w)
        except tk.TclError:
            pass


class ProxyText(_ProxyMixin, tk.Text):
    def __init__(self, master, **kw):
        tk.Text.__init__(self, master, **kw)
        self._install_proxy()


class PeerText(_ProxyMixin, tk.Text):

    def __init__(self, master, source, **kw):
        self.widgetName = "text"
        tk.BaseWidget._setup(self, master, {})
        source.peer_create(self._w, **kw)
        self._install_proxy()


class Document:
    def __init__(self, app, number):
        self.app = app
        self.id = uuid.uuid4().hex
        self.number = number
        self.path = None
        self.display_name = None
        self.encoding = "utf-8"
        self.eol = DEFAULT_EOL
        self.mtime = None
        self.lang = None
        self.lang_override = None
        self.kind = "text"
        self.read_only = False
        self.scratch = False
        self.remote = None
        self.pinned = False
        self.tab_color = None
        self.indent_spaces = app.use_spaces.get()
        self.indent_width = app.tab_width.get()
        self.words = 0
        self.chars = 0
        self.bookmarks = []
        self._bm_counter = 0
        self._fold_counter = 0
        self._fold_x = 10 ** 6
        self._refresh_job = None
        self._lines_job = None
        self._cursor_job = None
        self._undo_job = None
        self._minimap_job = None
        self._active = None
        self._mm = (1, 1.0)
        self.peer = None
        self.pane2 = None
        self.md_pane = None
        self.md_text = None
        self.lazy = None
        self.follow = None
        self.image = None
        self.image_source = None
        self.image_scale = 1
        self.git_base = None
        self.git_branch = None
        self.git_marks = {}
        self.syntax_error = None
        self.word_goal = 0
        self.filter_pattern = None
        self.snippet = None
        self.colsel = None
        self.vim_mode = "normal"
        self.vim_pending = ""
        self.undo_snaps = []
        self.undo_prev = []
        self.sql_db = None
        self.mixed_eol = False
        self.symbols = []

        self.frame = tk.PanedWindow(app.nb, orient="horizontal", bd=0, sashwidth=6,
                                    sashrelief="flat")
        self.vpane = tk.PanedWindow(self.frame, orient="vertical", bd=0, sashwidth=6,
                                    sashrelief="flat")
        self.frame.add(self.vpane, stretch="always")
        self.pane1 = tk.Frame(self.vpane, bd=0)
        self.vpane.add(self.pane1, stretch="always")
        self.gutter = tk.Canvas(self.pane1, width=40, bd=0, highlightthickness=0)
        self.text = ProxyText(self.pane1, **self.text_options())
        self.minimap = tk.Canvas(self.pane1, width=90, bd=0, highlightthickness=0, cursor="hand2")
        self.sy = ttk.Scrollbar(self.pane1, orient="vertical", command=self.text.yview,
                                style="Editor.Vertical.TScrollbar")
        self.sx = ttk.Scrollbar(self.pane1, orient="horizontal", command=self.text.xview,
                                style="Editor.Horizontal.TScrollbar")
        self.text.configure(yscrollcommand=self._on_yscroll, xscrollcommand=self._on_xscroll)
        self.gutter.grid(row=0, column=0, sticky="ns")
        self.text.grid(row=0, column=1, sticky="nsew")
        self.minimap.grid(row=0, column=2, sticky="ns")
        self.sy.grid(row=0, column=3, sticky="ns")
        self.sx.grid(row=1, column=1, sticky="ew")
        self.pane1.rowconfigure(0, weight=1)
        self.pane1.columnconfigure(1, weight=1)
        if not app.gutter_visible():
            self.gutter.grid_remove()
        if not app.show_minimap.get():
            self.minimap.grid_remove()
        self.ruler = tk.Frame(self.text, width=1, bd=0)

        t = self.text
        for name in ("curline", "guide", "ws_space", "ws_tab", "longline", "trail", "occur",
                     "bracket", "colsel", "find_all"):
            t.tag_configure(name)
        for name in TOKEN_GROUP_NAMES:
            t.tag_configure("tok_" + name)
        for i in range(6):
            t.tag_configure(f"rb{i}")
        t.tag_configure("syntax_error", underline=True)
        t.tag_configure("dim")
        t.tag_configure("filtered_out", elide=True)
        self._setup_view(t)
        self.gutter.bind("<MouseWheel>", self._gutter_wheel)
        self.gutter.bind("<Button-4>", lambda e: self.text.yview_scroll(-3, "units"))
        self.gutter.bind("<Button-5>", lambda e: self.text.yview_scroll(3, "units"))
        self.gutter.bind("<Button-1>", self._gutter_click)
        self.minimap.bind("<Button-1>", self._minimap_click)
        self.minimap.bind("<B1-Motion>", self._minimap_click)
        self.minimap.bind("<Configure>", lambda e: self.schedule_minimap())
        self.minimap.bind("<MouseWheel>", self._gutter_wheel)
        self.apply_theme()

    def text_options(self):
        app = self.app
        return dict(wrap="word" if app.wrap.get() else "none", undo=True, maxundo=-1,
                    font=app.font, borderwidth=0, highlightthickness=0, padx=8, pady=6,
                    tabs=(max(1, app.font.measure(" " * self.indent_width)),))

    def _setup_view(self, w):
        app = self.app
        w.on_change = self._on_change
        w.on_cursor = self._on_cursor
        w.tag_raise("sel")
        app.view_docs[str(w)] = self
        w.bindtags(("NotepadMacro",) + w.bindtags())
        w.bind("<<Modified>>", lambda e: app.update_tab(self))
        w.bind("<FocusIn>", lambda e, v=w: self._set_active(v))
        w.bind("<Return>", self._on_return)
        w.bind("<KP_Enter>", self._on_return)
        w.bind("<Tab>", self._on_tab)
        for seq in ("<Shift-Tab>", "<ISO_Left_Tab>"):
            try:
                w.bind(seq, self._on_shift_tab)
            except tk.TclError:
                pass
        w.bind("<BackSpace>", self._on_backspace)
        for ch, keysym in OPEN_KEYS.items():
            w.bind(f"<KeyPress-{keysym}>", lambda e, c=ch: self._on_open_char(e, c))
        for ch, keysym in CLOSE_KEYS.items():
            w.bind(f"<KeyPress-{keysym}>", lambda e, c=ch: self._on_close_char(e, c))
        w.bind("<KeyPress-greater>", self._on_greater)
        w.bind("<Escape>", self._on_escape)
        for ev in ("<<Undo>>", "<<Redo>>"):
            w.bind(ev, lambda e: "break" if self.read_only else None)
        w.bind("<<Copy>>", lambda e: app.after_copy(), add="+")
        w.bind("<<Cut>>", lambda e: app.after_copy(), add="+")
        w.bind("<<Paste>>", app.before_paste, add="+")
        w.bind("<Control-MouseWheel>", app.on_ctrl_wheel)
        w.bind("<Control-Button-4>", app.on_ctrl_wheel)
        w.bind("<Control-Button-5>", app.on_ctrl_wheel)
        w.bind("<Button-2>" if app.aqua else "<Button-3>", app.show_context_menu)
        w.bind("<Control-Button-1>", app.on_ctrl_click)
        for seq in ("<Alt-Button-1>", "<Shift-Alt-Button-1>"):
            w.bind(seq, app.column_start)
        for seq in ("<Alt-B1-Motion>", "<Shift-Alt-B1-Motion>"):
            w.bind(seq, app.column_drag)
        w.bind("<Button-1>", app.column_cancel_click, add="+")
        w.bind("<Motion>", app.on_hover)
        w.bind("<Leave>", app.hide_tooltip)
        app.bind_shortcuts(w)
        app.apply_vim_tags(self, w)

    def name(self):
        if self.display_name:
            return self.display_name
        if self.path:
            return os.path.basename(self.path)
        return "Untitled" if self.number == 1 else f"Untitled {self.number}"

    def modified(self):
        return bool(self.text.edit_modified())

    def content(self):
        return self.text.get("1.0", "end-1c")

    def is_blank(self):
        return (self.path is None and self.display_name is None and self.kind == "text"
                and not self.modified() and not self.content())

    def views(self):
        return [self.text] + ([self.peer] if self.peer else [])

    def view(self):
        return self._active if self._active in self.views() else self.text

    def _set_active(self, widget):
        self._active = widget
        self._on_cursor()

    def set_content(self, content):
        t = self.text
        if self.read_only:
            t.config(state="normal")
        self.clear_bookmarks()
        self.unfold_all()
        t.tag_remove("filtered_out", "1.0", "end")
        self.filter_pattern = None
        self.colsel = None
        self.snippet = None
        t.delete("1.0", "end")
        t.insert("1.0", content)
        t.edit_reset()
        t.edit_modified(False)
        t.mark_set("insert", "1.0")
        t.see("1.0")
        if self.read_only:
            t.config(state="disabled")

    def load(self, path, content, encoding, size):
        crlf = content.count("\r\n")
        cr = content.count("\r") - crlf
        lf = content.count("\n") - crlf
        self.mixed_eol = sum(1 for c in (crlf, cr, lf) if c) > 1
        self.eol = detect_eol(content)
        content = content.replace("\r\n", "\n").replace("\r", "\n")
        self.path = path
        self.encoding = encoding
        try:
            self.mtime = os.path.getmtime(path) if path else None
        except OSError:
            self.mtime = None
        self.set_content(content)
        if self.app.detect_indent.get():
            found = detect_indentation(content)
            if found:
                self.indent_spaces = found[0]
                if found[1]:
                    self.indent_width = found[1]
                self.apply_options()
        self.setup_language()
        self.undo_snaps = [content] if len(content) <= UNDO_MAX_DOC else []
        self.app.update_tab(self)
        lines = content.count("\n") + 1
        message = f"{path or self.name()}   |   {lines:,} lines   |   {size:,} bytes"
        if self.mixed_eol:
            message += "   |   Warning: mixed line endings (they will be unified on save)"
        self.app.set_message(message)

    def setup_language(self):
        if self.lang_override == "text":
            self.lang = None
        elif self.lang_override:
            self.lang = self.lang_override
        else:
            self.lang = detect_language(self.display_name or self.path)
        self.schedule_refresh(0)

    def set_read_only(self, flag):
        self.read_only = flag
        for w in self.views():
            w.config(state="disabled" if flag else "normal")
        self.app.update_tab(self)

    def bookmark_lines(self):
        return sorted({int(self.text.index(m).split(".")[0]) for m in self.bookmarks})

    def clear_bookmarks(self):
        for m in self.bookmarks:
            self.text.mark_unset(m)
        self.bookmarks = []
        self.redraw_gutter()

    def set_bookmark_lines(self, lines):
        self.clear_bookmarks()
        last = int(self.text.index("end-1c").split(".")[0])
        for line in lines:
            if line <= last:
                self._add_bookmark(line)
        self.redraw_gutter()

    def _add_bookmark(self, line):
        self._bm_counter += 1
        name = f"bookmark{self._bm_counter}"
        self.text.mark_set(name, f"{line}.0")
        self.text.mark_gravity(name, "left")
        self.bookmarks.append(name)

    def toggle_bookmark(self, line):
        found = [m for m in self.bookmarks if int(self.text.index(m).split(".")[0]) == line]
        for m in found:
            self.text.mark_unset(m)
            self.bookmarks.remove(m)
        if not found:
            self._add_bookmark(line)
        self.redraw_gutter()
        return not found

    def _indent(self, line_text):
        lead = re.match(r"[ \t]*", line_text).group()
        return len(lead.expandtabs(self.indent_width))

    def _line(self, n):
        return self.text.get(f"{n}.0", f"{n}.end")

    def last_line(self):
        return int(self.text.index("end-1c").split(".")[0])

    def is_foldable(self, line):
        cur = self._line(line)
        if not cur.strip():
            return False
        base = self._indent(cur)
        last = self.last_line()
        n = line + 1
        while n <= last and n <= line + 50:
            s = self._line(n)
            if s.strip():
                return self._indent(s) > base
            n += 1
        return False

    def fold_range(self, line):
        if not self.is_foldable(line):
            return None
        base = self._indent(self._line(line))
        last = self.last_line()
        end = line
        n = line + 1
        while n <= last:
            s = self._line(n)
            if s.strip():
                if self._indent(s) <= base:
                    break
                end = n
            n += 1
        return end if end > line else None

    def fold_starting_at(self, line):
        t = self.text
        idx = t.index(f"{line}.end")
        for tag in t.tag_names(idx):
            if tag.startswith("fold"):
                rng = t.tag_prevrange(tag, f"{idx}+1c")
                if rng and t.compare(rng[0], "==", idx):
                    return tag, int(t.index(f"{rng[1]}").split(".")[0])
        return None

    def _parent_line(self, line):
        cur = self._line(line)
        n = line
        while not cur.strip() and n < self.last_line():
            n += 1
            cur = self._line(n)
        base = self._indent(cur)
        n = line - 1
        while n >= 1:
            s = self._line(n)
            if s.strip() and self._indent(s) < base:
                return n
            n -= 1
        return None

    def add_fold(self, line, end):
        self._fold_counter += 1
        tag = f"fold{self._fold_counter}"
        t = self.text
        t.tag_configure(tag, elide=True)
        t.tag_add(tag, f"{line}.end", f"{end}.end")
        for w in self.views():
            if t.compare(w.index("insert"), ">", f"{line}.end") and \
                    t.compare(w.index("insert"), "<=", f"{end}.end"):
                w.mark_set("insert", f"{line}.end")

    def toggle_fold(self, line):
        found = self.fold_starting_at(line)
        if found:
            self.text.tag_delete(found[0])
            self.redraw_gutter()
            return False
        end = self.fold_range(line)
        if end is None:
            parent = self._parent_line(line)
            if parent is None:
                return None
            found = self.fold_starting_at(parent)
            if found:
                self.text.tag_delete(found[0])
                self.redraw_gutter()
                return False
            end = self.fold_range(parent)
            if end is None:
                return None
            line = parent
        self.add_fold(line, end)
        self.redraw_gutter()
        return True

    def fold_all(self):
        for line in range(self.last_line(), 0, -1):
            if not self.fold_starting_at(line):
                end = self.fold_range(line)
                if end:
                    self.add_fold(line, end)
        self.redraw_gutter()

    def unfold_all(self):
        for tag in self.text.tag_names():
            if tag.startswith("fold"):
                self.text.tag_delete(tag)
        self.redraw_gutter()

    def reveal(self, index):
        t = self.text
        changed = False
        for tag in t.tag_names(index):
            if tag.startswith("fold"):
                t.tag_delete(tag)
                changed = True
            elif tag == "filtered_out":
                t.tag_remove(tag, f"{index} linestart", f"{index} lineend+1c")
                changed = True
        if changed:
            self.redraw_gutter()

    def _elided_end(self, n):
        t = self.text
        idx = f"{n}.0"
        end = None
        for tag in t.tag_names(idx):
            if tag.startswith("fold") or tag == "filtered_out":
                rng = t.tag_prevrange(tag, f"{idx}+1c")
                if rng:
                    line = int(t.index(f"{rng[1]}-1c").split(".")[0])
                    end = line if end is None else max(end, line)
        return end

    def toggle_split(self):
        if self.peer:
            self._active = self.text
            self.vpane.forget(self.pane2)
            self.app.view_docs.pop(str(self.peer), None)
            self.peer.destroy()
            self.pane2.destroy()
            self.peer = self.pane2 = None
            self.text.focus_set()
            return False
        self.pane2 = tk.Frame(self.vpane, bd=0)
        self.peer = PeerText(self.pane2, self.text, **self.text_options())
        sy = ttk.Scrollbar(self.pane2, orient="vertical", command=self.peer.yview,
                           style="Editor.Vertical.TScrollbar")
        sx = ttk.Scrollbar(self.pane2, orient="horizontal", command=self.peer.xview,
                           style="Editor.Horizontal.TScrollbar")
        self.peer.configure(yscrollcommand=sy.set, xscrollcommand=sx.set)
        self.peer.grid(row=0, column=0, sticky="nsew")
        sy.grid(row=0, column=1, sticky="ns")
        sx.grid(row=1, column=0, sticky="ew")
        self.pane2.rowconfigure(0, weight=1)
        self.pane2.columnconfigure(0, weight=1)
        self._setup_view(self.peer)
        if self.read_only:
            self.peer.config(state="disabled")
        self.vpane.add(self.pane2, stretch="always")
        self.apply_theme()
        self.peer.mark_set("insert", self.text.index("insert"))
        self.peer.yview_moveto(self.text.yview()[0])
        self.vpane.update_idletasks()
        try:
            self.vpane.sash_place(0, 0, max(60, self.vpane.winfo_height() // 2))
        except tk.TclError:
            pass
        self.peer.focus_set()
        return True

    def toggle_md_preview(self):
        if self.md_pane:
            self.frame.forget(self.md_pane)
            self.md_pane.destroy()
            self.md_pane = self.md_text = None
            return False
        self.md_pane = tk.Frame(self.frame, bd=0)
        self.md_text = tk.Text(self.md_pane, wrap="word", bd=0, highlightthickness=0, padx=14,
                               pady=10, cursor="arrow", state="disabled")
        sb = ttk.Scrollbar(self.md_pane, command=self.md_text.yview,
                           style="Editor.Vertical.TScrollbar")
        self.md_text.config(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self.md_text.pack(side="left", fill="both", expand=True)
        self.frame.add(self.md_pane, stretch="always")
        self.apply_theme()
        self.frame.update_idletasks()
        try:
            self.frame.sash_place(0, max(200, self.frame.winfo_width() // 2), 0)
        except tk.TclError:
            pass
        self.update_md_preview()
        return True

    def update_md_preview(self, content=None):
        if not self.md_text:
            return
        top = self.md_text.yview()[0]
        links = md_render(self.md_text, self.content() if content is None else content)
        for tag, url in links:
            self.md_text.tag_bind(tag, "<Button-1>", lambda e, u=url: self.app.open_link(u, self))
        self.md_text.yview_moveto(top)

    def apply_theme(self):
        app = self.app
        th = app.theme
        for w in self.views():
            w.config(bg=th["bg"], fg=th["fg"], insertbackground=th["cursor"],
                     selectbackground=th["sel_bg"], selectforeground=th["sel_fg"],
                     inactiveselectbackground=th["sel_bg"])
        self.frame.config(bg=th["border"])
        self.vpane.config(bg=th["border"])
        self.pane1.config(bg=th["bg"])
        self.gutter.config(bg=th["gutter_bg"])
        self.minimap.config(bg=th["gutter_bg"])
        self.ruler.config(bg=th["ruler"])
        t = self.text
        t.tag_configure("curline", background=th["curline"])
        t.tag_configure("guide", background=th["guide"])
        t.tag_configure("ws_space", background=th["ws"])
        t.tag_configure("ws_tab", background=th["ws_tab"])
        t.tag_configure("longline", background=th["long"])
        t.tag_configure("trail", background=th["trail"])
        t.tag_configure("occur", background=th["occur"])
        t.tag_configure("bracket", background=th["bracket"])
        t.tag_configure("colsel", background=th["colsel"], foreground=th["sel_fg"])
        t.tag_configure("find_all", background=th["find_all"])
        for name in TOKEN_GROUP_NAMES:
            t.tag_configure("tok_" + name, foreground=th[name])
        colors = th["rainbow"]
        for i in range(6):
            t.tag_configure(f"rb{i}", foreground=colors[i % len(colors)])
        t.tag_configure("syntax_error", background=th["syntax_error"])
        t.tag_configure("dim", foreground=th["dim"])
        for tag in ("colsel", "find_all", "syntax_error", "dim"):
            t.tag_raise(tag)
        t.tag_raise("sel")
        if self.md_text:
            md = self.md_text
            base = tkfont.Font(font=app.font).actual()
            family = "TkDefaultFont"
            size = app.font_size
            md.config(bg=th["bg"], fg=th["fg"], selectbackground=th["sel_bg"],
                      selectforeground=th["sel_fg"], font=(family, size))
            for level, scale in ((1, 1.8), (2, 1.5), (3, 1.25), (4, 1.1)):
                md.tag_configure(f"md_h{level}", font=(family, round(size * scale), "bold"),
                                 foreground=th["keyword"], spacing1=8, spacing3=4)
            md.tag_configure("md_b", font=(family, size, "bold"))
            md.tag_configure("md_i", font=(family, size, "italic"))
            md.tag_configure("md_s", overstrike=True)
            md.tag_configure("md_icode", font=(base["family"], size), background=th["code_bg"],
                             foreground=th["string"])
            md.tag_configure("md_code", font=(base["family"], size), background=th["code_bg"],
                             lmargin1=12, lmargin2=12)
            md.tag_configure("md_quote", foreground=th["comment"], lmargin1=16, lmargin2=16)
            md.tag_configure("md_li", lmargin1=8, lmargin2=24)
            md.tag_configure("md_table", font=(base["family"], size))
            md.tag_configure("md_hr", foreground=th["gutter_fg"])
            md.tag_configure("md_link", foreground=th["link"], underline=True)
            md.tag_bind("md_link", "<Enter>", lambda e: self.md_text.config(cursor="hand2"))
            md.tag_bind("md_link", "<Leave>", lambda e: self.md_text.config(cursor="arrow"))
        self.update_ruler()
        self.redraw_gutter()
        self.schedule_minimap()

    def apply_options(self):
        tabs = (max(1, self.app.font.measure(" " * self.indent_width)),)
        for w in self.views():
            w.config(wrap="word" if self.app.wrap.get() else "none", tabs=tabs)
        self.update_ruler()
        self.schedule_gutter()
        self.schedule_refresh(50)

    def update_ruler(self):
        app = self.app
        if not app.show_ruler.get() or self.kind != "text":
            self.ruler.place_forget()
            return
        info = None
        try:
            info = self.text.dlineinfo("@0,0")
        except tk.TclError:
            pass
        x0 = info[0] if info else int(str(self.text.cget("padx")))
        x = x0 + app.font.measure("0") * app.ruler_col.get()
        self.ruler.place(in_=self.text, x=x, y=0, relheight=1, width=1)

    def redraw_gutter(self):
        if not self.app.gutter_visible():
            return
        g, t = self.gutter, self.text
        font = self.app.font
        last = self.last_line()
        cw = font.measure("0")
        mark_w = font.measure("●") + 4
        num_right = mark_w + cw * max(3, len(str(last)))
        width = num_right + cw + 12
        self._fold_x = num_right + 2
        if int(g.cget("width")) != width:
            g.config(width=width)
        g.delete("all")
        th = self.app.theme
        height = t.winfo_height()
        marks = set(self.bookmark_lines())
        err_line = self.syntax_error[0] if self.syntax_error else None
        try:
            cur_line = int(self.view().index("insert").split(".")[0])
        except tk.TclError:
            cur_line = None
        try:
            n = int(t.index("@0,0").split(".")[0])
        except tk.TclError:
            return
        while n <= last:
            jump = self._elided_end(n)
            if jump is not None and jump >= n:
                n = jump + 1
                continue
            info = t.dlineinfo(f"{n}.0")
            if info is None:
                break
            y = info[1]
            if y > height:
                break
            color = (th["error"] if n == err_line else
                     th["fg"] if n == cur_line and self.kind == "text" else th["gutter_fg"])
            g.create_text(num_right, y, anchor="ne", text=str(n), font=font, fill=color)
            if n in marks:
                g.create_text(2, y, anchor="nw", text="●", font=font, fill=th["bookmark"])
            folded = self.fold_starting_at(n)
            if folded:
                g.create_text(num_right + 4, y, anchor="nw", text="▸", font=font,
                              fill=th["bookmark"])
            elif self.kind == "text" and self.is_foldable(n):
                g.create_text(num_right + 4, y, anchor="nw", text="▾", font=font,
                              fill=th["gutter_fg"])
            mark = self.git_marks.get(n)
            if mark:
                g.create_rectangle(width - 3, y, width, y + info[3], fill=th["git_" + mark],
                                   width=0)
            n = folded[1] + 1 if folded else n + 1

    def _gutter_click(self, event):
        index = self.text.index(f"@0,{event.y}")
        line = int(index.split(".")[0])
        if event.x >= self._fold_x:
            self.toggle_fold(line)
        else:
            self.toggle_bookmark(line)

    def schedule_minimap(self):
        if self._minimap_job is None and self.app.show_minimap.get():
            self._minimap_job = self.text.after(120, self.redraw_minimap)

    def redraw_minimap(self):
        self._minimap_job = None
        c = self.minimap
        c.delete("all")
        if not self.app.show_minimap.get():
            return
        th = self.app.theme
        height = max(1, c.winfo_height())
        width = int(str(c.cget("width")))
        lines = self.content().split("\n")
        n = len(lines)
        scale = min(2.0, height / max(1, n))
        step = max(1, int(1 / scale)) if scale < 1 else 1
        for i in range(0, n, step):
            line = lines[i].expandtabs(4)
            stripped = line.lstrip()
            if not stripped:
                continue
            ind = len(line) - len(stripped)
            x1 = 4 + min(width - 10, ind * 0.6)
            x2 = min(width - 4, x1 + max(1.0, len(stripped) * 0.6))
            y = i * scale
            c.create_rectangle(x1, y, x2, y + max(1.0, scale * 0.7), fill=th["minimap_fg"],
                               width=0)
        self._mm = (n, scale)
        first, last = self.text.yview()
        c.create_rectangle(1, first * n * scale, width - 1, max(first * n * scale + 4,
                           last * n * scale), outline=th["minimap_view"], width=1, tags="view")

    def _move_minimap_view(self, first, last):
        n, scale = self._mm
        if self.app.show_minimap.get() and self.minimap.find_withtag("view"):
            width = int(str(self.minimap.cget("width")))
            self.minimap.coords("view", 1, first * n * scale, width - 1,
                                max(first * n * scale + 4, last * n * scale))

    def _minimap_click(self, event):
        n, scale = self._mm
        total = max(1.0, n * scale)
        first, last = self.text.yview()
        self.text.yview_moveto(max(0.0, event.y / total - (last - first) / 2))

    def highlight(self):
        t = self.text
        for name in TOKEN_GROUP_NAMES:
            t.tag_remove("tok_" + name, "1.0", "end")
        for i in range(6):
            t.tag_remove(f"rb{i}", "1.0", "end")
        for tag in t.tag_names():
            if tag.startswith("sw_"):
                t.tag_delete(tag)
        if self.kind != "text" or not self.app.highlight.get():
            return
        content = self.content()
        if len(content) > HIGHLIGHT_LIMIT:
            return
        index = make_indexer(content)
        skip = []
        if self.lang:
            ranges = {}
            for m in LANGUAGES[self.lang].finditer(content):
                if m.end() > m.start():
                    group = m.lastgroup.rsplit("_", 1)[0]
                    ranges.setdefault(group, []).extend((index(m.start()), index(m.end())))
                    if group in ("string", "comment"):
                        skip.append((m.start(), m.end()))
            for group, idx in ranges.items():
                for i in range(0, len(idx), 2000):
                    t.tag_add("tok_" + group, *idx[i:i + 2000])
        if self.app.rainbow.get() and self.lang and self.lang not in ("markdown", "log", "http"):
            self._rainbow(content, index, skip)
        if self.app.swatches.get() and self.lang in SWATCH_LANGS:
            self._swatches(content, index)
        t.tag_raise("sel")

    def _rainbow(self, content, index, skip):
        starts = [s for s, _ in skip]
        colors = len(self.app.theme["rainbow"])
        stack = []
        out = {}
        for m in re.finditer(r"[()\[\]{}]", content):
            p = m.start()
            k = bisect.bisect_right(starts, p) - 1
            if k >= 0 and skip[k][0] <= p < skip[k][1]:
                continue
            if m.group() in "([{":
                level = len(stack) % colors
                stack.append(level)
            else:
                level = stack.pop() if stack else 0
            out.setdefault(level, []).extend((index(p), index(p + 1)))
        for level, idx in out.items():
            for i in range(0, len(idx), 2000):
                self.text.tag_add(f"rb{level}", *idx[i:i + 2000])

    def _swatches(self, content, index):
        t = self.text
        found = {}
        for m in re.finditer(r"#(?:[0-9a-fA-F]{6}|[0-9a-fA-F]{3})(?![0-9a-zA-Z_])", content):
            value = m.group()[1:]
            if len(value) == 3:
                value = "".join(c * 2 for c in value)
            tag = "sw_" + value.upper()
            if tag not in found:
                if len(found) >= 300:
                    break
                fg = "#000000" if luminance("#" + value) > 0.5 else "#FFFFFF"
                t.tag_configure(tag, background="#" + value, foreground=fg)
                found[tag] = []
            found[tag].extend((index(m.start()), index(m.end())))
        for tag, idx in found.items():
            for i in range(0, len(idx), 2000):
                t.tag_add(tag, *idx[i:i + 2000])

    def decorate(self, content=None):
        t = self.text
        for tag in ("guide", "ws_space", "ws_tab", "trail", "longline"):
            t.tag_remove(tag, "1.0", "end")
        app = self.app
        if self.kind != "text":
            return
        flags = (app.show_guides.get(), app.show_ws.get(), app.show_trailing.get(),
                 app.mark_long.get())
        if not any(flags):
            return
        content = self.content() if content is None else content
        if len(content) > HIGHLIGHT_LIMIT:
            return
        index = make_indexer(content)
        out = {"guide": [], "ws_space": [], "ws_tab": [], "trail": [], "longline": []}
        if app.show_ws.get():
            for m in re.finditer(r" +|\t+", content):
                key = "ws_space" if m.group()[0] == " " else "ws_tab"
                out[key].extend((index(m.start()), index(m.end())))
        if app.show_trailing.get():
            cursor_line = int(self.view().index("insert").split(".")[0])
            for m in re.finditer(r"[ \t]+$", content, re.MULTILINE):
                start = index(m.start())
                if int(start.split(".")[0]) != cursor_line:
                    out["trail"].extend((start, index(m.end())))
        width = max(1, self.indent_width)
        limit = app.ruler_col.get()
        guides = app.show_guides.get()
        long_lines = app.mark_long.get()
        offset = 0
        for line in content.split("\n"):
            if guides and line[:1] in (" ", "\t") and line.strip():
                lead = line[:len(line) - len(line.lstrip(" \t"))]
                col = 0
                for i, ch in enumerate(lead):
                    if ch == "\t" or col % width == 0:
                        out["guide"].extend((index(offset + i), index(offset + i + 1)))
                    col = col + width - col % width if ch == "\t" else col + 1
            if long_lines and len(line) > limit:
                out["longline"].extend((index(offset + limit), index(offset + len(line))))
            offset += len(line) + 1
        for tag, idx in out.items():
            for i in range(0, len(idx), 2000):
                t.tag_add(tag, *idx[i:i + 2000])

    def match_brackets(self):
        t = self.text
        w = self.view()
        t.tag_remove("bracket", "1.0", "end")
        opens = {"(": ")", "[": "]", "{": "}"}
        closes = {v: k for k, v in opens.items()}
        for idx in ("insert-1c", "insert"):
            ch = w.get(idx)
            if ch in opens or ch in closes:
                break
        else:
            return
        pos = w.index(idx)
        other = None
        depth = 0
        if ch in opens:
            close = opens[ch]
            for i, c in enumerate(t.get(pos, f"{pos}+{BRACKET_LIMIT}c")):
                if c == ch:
                    depth += 1
                elif c == close:
                    depth -= 1
                    if depth == 0:
                        other = f"{pos}+{i}c"
                        break
        else:
            open_ = closes[ch]
            chunk = t.get(f"{pos}-{BRACKET_LIMIT}c", f"{pos}+1c")
            for i, c in enumerate(reversed(chunk)):
                if c == ch:
                    depth += 1
                elif c == open_:
                    depth -= 1
                    if depth == 0:
                        other = f"{pos}-{i}c"
                        break
        if other:
            t.tag_add("bracket", pos, f"{pos}+1c", other, f"{other}+1c")

    def highlight_current_line(self):
        t, w = self.text, self.view()
        t.tag_remove("curline", "1.0", "end")
        if self.app.hl_line.get() and not w.tag_ranges("sel") and self.kind == "text":
            idx = w.index("insert")
            t.tag_add("curline", f"{idx} linestart", f"{idx} lineend+1c")

    def highlight_occurrences(self):
        t, w = self.text, self.view()
        t.tag_remove("occur", "1.0", "end")
        if not self.app.hl_occ.get() or not w.tag_ranges("sel"):
            return
        word = w.get("sel.first", "sel.last")
        if not re.fullmatch(r"\w{2,}", word):
            return
        content = self.content()
        if len(content) > HIGHLIGHT_LIMIT:
            return
        index = make_indexer(content)
        ranges = []
        for count, m in enumerate(re.finditer(rf"\b{re.escape(word)}\b", content)):
            if count >= OCCURRENCE_LIMIT:
                break
            ranges.extend((index(m.start()), index(m.end())))
        for i in range(0, len(ranges), 2000):
            t.tag_add("occur", *ranges[i:i + 2000])

    def focus_dim(self):
        t, w = self.text, self.view()
        t.tag_remove("dim", "1.0", "end")
        if not self.app.focus_mode.get() or self.kind != "text":
            return
        line = int(w.index("insert").split(".")[0])
        last = self.last_line()
        start = line
        while start > 1 and self._line(start - 1).strip():
            start -= 1
        end = line
        while end < last and self._line(end + 1).strip():
            end += 1
        t.tag_add("dim", "1.0", f"{start}.0")
        t.tag_add("dim", f"{end}.end", "end")

    def typewriter_scroll(self):
        if not self.app.typewriter.get():
            return
        w = self.view()
        info = w.dlineinfo("insert")
        if not info:
            w.see("insert")
            info = w.dlineinfo("insert")
            if not info:
                return
        delta = info[1] + info[3] // 2 - w.winfo_height() // 2
        if abs(delta) > info[3]:
            w.yview_scroll(delta, "pixels")

    def _on_yscroll(self, first, last):
        self.sy.set(first, last)
        self.redraw_gutter()
        self._move_minimap_view(float(first), float(last))
        if self.lazy and float(last) > 0.98 and not self.lazy.get("done"):
            self.text.after_idle(self.app.load_more, self)

    def _on_xscroll(self, first, last):
        self.sx.set(first, last)
        self.update_ruler()

    def _on_change(self):
        self.schedule_gutter()
        self.schedule_refresh(250)
        if self._undo_job is None and self.kind == "text":
            self._undo_job = self.text.after(1500, self._snapshot)

    def _snapshot(self):
        self._undo_job = None
        content = self.content()
        if len(content) > UNDO_MAX_DOC:
            return
        if not self.undo_snaps or self.undo_snaps[-1] != content:
            self.undo_snaps.append(content)
            del self.undo_snaps[:-UNDO_SNAPSHOTS]

    def schedule_gutter(self):
        if self._lines_job is None:
            self._lines_job = self.text.after_idle(self._lines_idle)

    def _lines_idle(self):
        self._lines_job = None
        self.redraw_gutter()

    def _on_cursor(self):
        if self._cursor_job is None:
            self._cursor_job = self.text.after_idle(self._cursor_idle)

    def _cursor_idle(self):
        self._cursor_job = None
        self.match_brackets()
        self.highlight_current_line()
        self.highlight_occurrences()
        self.focus_dim()
        self.typewriter_scroll()
        self.redraw_gutter()
        if self.app.current() is self:
            self.app.update_status()

    def schedule_refresh(self, delay):
        if self._refresh_job:
            self.text.after_cancel(self._refresh_job)
        self._refresh_job = self.text.after(delay, self.refresh)

    def refresh(self):
        self._refresh_job = None
        self.highlight()
        content = self.content()
        self.decorate(content)
        self.chars = len(content)
        self.words = len(content.split())
        self.redraw_gutter()
        self.schedule_minimap()
        self.app.after_doc_refresh(self, content)

    def _md_continue(self, w):
        if w.tag_ranges("sel") or w.compare("insert", "!=", "insert lineend"):
            return False
        line = w.get("insert linestart", "insert lineend")
        m = re.match(r"^(\s*)([-*+]|\d+[.)])(\s+)(\[[ xX]\]\s+)?(.*)$", line)
        if not m:
            return False
        if not m.group(5).strip():
            w.delete("insert linestart", "insert lineend")
            w.insert("insert", m.group(1))
            return True
        marker = m.group(2)
        if marker[0].isdigit():
            marker = f"{int(marker[:-1]) + 1}{marker[-1]}"
        task = "[ ] " if m.group(4) else ""
        w.insert("insert", "\n" + m.group(1) + marker + m.group(3) + task)
        w.see("insert")
        return True

    def _on_return(self, event):
        app = self.app
        if self.read_only:
            return None
        w = event.widget
        self.snippet = None
        if self.lang == "markdown" and self._md_continue(w):
            return "break"
        if not app.auto_indent.get():
            return None
        if w.tag_ranges("sel"):
            w.delete("sel.first", "sel.last")
        line = w.get("insert linestart", "insert")
        indent = re.match(r"[ \t]*", line).group(0)
        openers = AUTO_INDENT_OPENERS.get(self.lang)
        stripped = line.rstrip()
        extra = bool(openers) and stripped.endswith(openers)
        if extra and self.lang in ("lua", "ruby"):
            extra = bool(re.search(r"\b(?:then|do)$", stripped))
        unit = app.indent_unit(self)
        prev, nxt = w.get("insert-1c"), w.get("insert")
        if extra and prev in "([{" and nxt == PAIRS.get(prev):
            w.insert("insert", "\n" + indent + unit + "\n" + indent)
            w.mark_set("insert", f"insert-{len(indent) + 1}c")
        elif self.lang == "markup" and prev == ">" and w.get("insert", "insert+2c") == "</":
            w.insert("insert", "\n" + indent + unit + "\n" + indent)
            w.mark_set("insert", f"insert-{len(indent) + 1}c")
        else:
            w.insert("insert", "\n" + indent + (unit if extra else ""))
        w.see("insert")
        return "break"

    def _on_tab(self, event):
        app = self.app
        w = event.widget
        if self.read_only:
            return "break"
        if self.snippet and app.snippet_next(self, w):
            return "break"
        if w.tag_ranges("sel"):
            first, last = selected_lines(w)
            whole_line = (w.index("sel.first").endswith(".0")
                          and w.compare("sel.last", ">=", f"{last}.end"))
            if first != last or whole_line:
                app.indent_lines(self, w, dedent=False)
                return "break"
            w.delete("sel.first", "sel.last")
        elif app.expand_snippet(self, w):
            return "break"
        elif self.lang == "markup" and app.expand_emmet(self, w):
            return "break"
        if self.indent_spaces:
            width = self.indent_width
            col = len(w.get("insert linestart", "insert").expandtabs(width))
            w.insert("insert", " " * (width - col % width))
        else:
            w.insert("insert", "\t")
        w.see("insert")
        return "break"

    def _on_shift_tab(self, event):
        if not self.read_only:
            self.app.indent_lines(self, event.widget, dedent=True)
        return "break"

    def _on_backspace(self, event):
        app = self.app
        w = event.widget
        if self.read_only or w.tag_ranges("sel") or w.compare("insert", "==", "1.0"):
            return None
        prev, nxt = w.get("insert-1c"), w.get("insert")
        if app.auto_close.get() and prev in PAIRS and PAIRS[prev] == nxt:
            w.delete("insert-1c", "insert+1c")
            return "break"
        before = w.get("insert linestart", "insert")
        width = self.indent_width
        if self.indent_spaces and before and before.strip(" ") == "" and len(before) > 1:
            count = (len(before) - 1) % width + 1
            w.delete(f"insert-{count}c", "insert")
            return "break"
        return None

    def _on_open_char(self, event, ch):
        app = self.app
        w = event.widget
        if self.read_only or not app.auto_close.get():
            return None
        quote = ch in "\"'`"
        if quote and not self.lang:
            return None
        if ch == "`" and self.lang not in ("clike", "markdown", "shell", "sql"):
            return None
        if ch == "'" and self.lang in ("markdown", "yaml", "log"):
            return None
        close = PAIRS[ch]
        if w.tag_ranges("sel"):
            first, last = w.index("sel.first"), w.index("sel.last")
            inner = w.get(first, last)
            app.edit_block(self, w, first, last, ch + inner + close, keep_cursor=False)
            w.tag_add("sel", f"{first}+1c", f"{first}+{1 + len(inner)}c")
            w.mark_set("insert", f"{first}+{1 + len(inner)}c")
            return "break"
        nxt = w.get("insert")
        if quote:
            if nxt == ch:
                w.mark_set("insert", "insert+1c")
                return "break"
            before = re.search(r"\w*$", w.get("insert linestart", "insert")).group()
            if before and before.lower() not in STRING_PREFIXES:
                return None
            if w.get("insert-1c") == "\\":
                return None
        if nxt and not (nxt.isspace() or nxt in ")]}>,;:"):
            return None
        w.insert("insert", ch + close)
        w.mark_set("insert", "insert-1c")
        return "break"

    def _on_close_char(self, event, ch):
        w = event.widget
        if (not self.read_only and self.app.auto_close.get()
                and not w.tag_ranges("sel") and w.get("insert") == ch):
            w.mark_set("insert", "insert+1c")
            return "break"
        return None

    def _on_greater(self, event):
        w = event.widget
        if self.read_only or self.lang != "markup" or not self.app.auto_close.get():
            return None
        if w.tag_ranges("sel"):
            return None
        before = w.get("insert linestart", "insert")
        m = re.search(r"<([A-Za-z][\w:.-]*)(?:\s[^<>]*)?$", before)
        if not m or before.endswith("/") or m.group(1).lower() in VOID_TAGS:
            return None
        if w.get("insert", f"insert+{len(m.group(1)) + 3}c") == f"</{m.group(1)}>":
            return None
        w.insert("insert", f"></{m.group(1)}>")
        w.mark_set("insert", f"insert-{len(m.group(1)) + 3}c")
        return "break"

    def _on_escape(self, event):
        self.snippet = None
        if self.colsel:
            self.app.column_clear(self)
        if self.app.find_bar_visible:
            self.app.hide_find_bar()
        return None

    def _gutter_wheel(self, event):
        self.text.yview_scroll(-3 if event.delta > 0 else 3, "units")
        return "break"

    def cancel_jobs(self):
        for job in (self._refresh_job, self._lines_job, self._cursor_job, self._undo_job,
                    self._minimap_job):
            if job:
                try:
                    self.text.after_cancel(job)
                except tk.TclError:
                    pass
        self._refresh_job = self._lines_job = self._cursor_job = None
        self._undo_job = self._minimap_job = None
        if self.follow and self.follow.get("job"):
            try:
                self.text.after_cancel(self.follow["job"])
            except tk.TclError:
                pass
            self.follow = None

    def destroy(self):
        self.cancel_jobs()
        for w in self.views():
            w.on_change = w.on_cursor = None
            self.app.view_docs.pop(str(w), None)
        self.frame.destroy()


class Notepad:
    def __init__(self, root):
        self.root = root
        self.cfg = load_config()
        self.docs = {}
        self.view_docs = {}
        self._untitled = 0
        self._checking = False
        self._drag_tab = None
        self._close_pressed = None
        self.find_win = None
        self.fif_win = None
        self.palette_win = None
        self.zen = False
        self.fullscreen = False
        self._zen_state = {}
        self.proc = None
        self._out_queue = None
        self._run_cwd = None
        self._run_started = 0
        self._reset_pending = False
        self.nav_back = []
        self.nav_fwd = []
        self.clip_history = []
        self.macro = []
        self.macro_recording = False
        self._macro_playing = False
        self.pomodoro = None
        self._tip = None
        self._tip_job = None
        self._tip_word = None
        self._server = None
        self._instance_queue = queue.Queue()
        self.preview_server = None
        self.preview_cache = {}
        self._tab_images = {}
        self._error_shown = False
        self._find_job = None
        self.find_bar_visible = False
        self._expand_stack = []
        self._theme_auto_job = None
        self.aqua = root.tk.call("tk", "windowingsystem") == "aqua"

        c = self.cfg
        self.themes = {}
        self.load_user_themes()
        self.theme_var = tk.StringVar(value=c["theme"] if c["theme"] in self.themes or
                                      c["theme"] == "Auto" else "Blue")
        self.theme = self.themes[self.resolve_theme_name()]
        self.font_size = self._clamp(c["font_size"])
        self.font = tkfont.Font(root, family=c["font_family"], size=self.font_size)

        def bvar(key):
            return tk.BooleanVar(value=bool(c[key]))

        self.wrap = bvar("wrap")
        self.auto_indent = bvar("auto_indent")
        self.line_numbers = bvar("line_numbers")
        self.highlight = bvar("highlight")
        self.tab_width = tk.IntVar(value=c["tab_width"] if c["tab_width"] in (2, 4, 8) else 4)
        self.use_spaces = bvar("use_spaces")
        self.auto_close = bvar("auto_close")
        self.hl_line = bvar("highlight_line")
        self.hl_occ = bvar("highlight_occurrences")
        self.trim_on_save = bvar("trim_on_save")
        self.restore_session = bvar("restore_session")
        self.show_minimap = bvar("show_minimap")
        self.show_guides = bvar("show_guides")
        self.show_ws = bvar("show_whitespace")
        self.show_trailing = bvar("show_trailing")
        self.mark_long = bvar("mark_long")
        self.show_ruler = bvar("show_ruler")
        self.rainbow = bvar("rainbow")
        self.swatches = bvar("swatches")
        self.typewriter = bvar("typewriter")
        self.focus_mode = bvar("focus_mode")
        self.auto_save = bvar("auto_save")
        self.backup_bak = bvar("backup_bak")
        self.detect_indent = bvar("detect_indent")
        self.single_instance = bvar("single_instance")
        self.vim_var = bvar("vim_mode")
        self.explorer_var = bvar("explorer")
        self.outline_var = bvar("outline")
        self.ruler_col = tk.IntVar(value=int(c.get("ruler_col") or 80))
        self.ui_scale = tk.StringVar(value=str(c.get("ui_scale") or "100"))
        self.topmost = tk.BooleanVar(value=False)
        self.ro_var = tk.BooleanVar(value=False)
        self.lang_var = tk.StringVar(value="auto")
        self.enc_var = tk.StringVar(value="utf-8")
        self.eol_var = tk.StringVar(value=EOL_NAMES[DEFAULT_EOL])
        self.find_var = tk.StringVar()
        self.replace_var = tk.StringVar()
        self.opt_case = bvar("match_case")
        self.opt_word = bvar("whole_word")
        self.opt_regex = bvar("regex")
        self.snippets = self.load_snippets(quiet=True)

        try:
            root.geometry(c["geometry"])
        except tk.TclError:
            root.geometry("900x600")
        if c.get("maximized"):
            try:
                root.state("zoomed")
            except tk.TclError:
                pass

        self._base_fonts = {}
        for name in ("TkDefaultFont", "TkTextFont", "TkMenuFont", "TkHeadingFont",
                     "TkCaptionFont", "TkSmallCaptionFont", "TkIconFont", "TkTooltipFont"):
            try:
                self._base_fonts[name] = tkfont.nametofont(name).cget("size")
            except tk.TclError:
                pass

        self._set_icon()
        self._build_commands()
        self._build_menu()
        self._build_context_menu()
        self._build_status_bar()
        self._build_find_bar()
        self._build_main()
        self._build_output_panel()
        self._build_console()
        self._build_side_panel()
        self._apply_chrome_theme()
        self.apply_ui_scale(save=False)
        self.bind_shortcuts(root)
        root.bind_class("NotepadColumn", "<KeyPress>", self.column_key)
        root.bind_class("NotepadVim", "<KeyPress>", self.vim_key)
        root.bind_class("NotepadMacro", "<KeyPress>", self._macro_capture)
        root.bind("<Escape>", lambda e: self.toggle_zen() if self.zen else None)
        root.protocol("WM_DELETE_WINDOW", self.exit)
        root.report_callback_exception = self.report_error
        threading.excepthook = lambda args: self.root.after(
            0, self.report_error, args.exc_type, args.exc_value, args.exc_traceback)

    @staticmethod
    def _clamp(size):
        try:
            return max(MIN_SIZE, min(MAX_SIZE, int(size)))
        except (TypeError, ValueError):
            return DEFAULT_SIZE

    def _set_icon(self):
        icon = tk.PhotoImage(width=32, height=32)
        icon.put("{#C0C0C0}", to=(4, 1, 28, 31))
        icon.put("{" + BG + "}", to=(5, 2, 27, 30))
        icon.put("{#FFFF55}", to=(5, 2, 27, 5))
        for y, end in ((9, 24), (13, 22), (17, 24), (21, 19), (25, 23)):
            icon.put("{" + FG + "}", to=(8, y, end, y + 2))
        self.icon = icon
        self.root.iconphoto(True, icon)

    def _build_shortcuts(self):
        self.shortcuts = []
        for cid in self.command_order:
            for seq in self.commands[cid]["keys"]:
                self.shortcuts.append((seq, cid))
                m = re.fullmatch(r"<((?:Control-|Alt-)+)([a-z])>", seq)
                if m:
                    self.shortcuts.append((f"<{m.group(1)}{m.group(2).upper()}>", cid))

    def bind_shortcuts(self, widget):
        for seq, cid in self.shortcuts:
            try:
                widget.bind(seq, lambda e, c=cid: self.run_command(c))
            except tk.TclError:
                pass

    def _build_menu(self):
        mb = tk.Menu(self.root)
        self.menubar = mb
        self.submenus = {}
        self.palette_items = []
        for title, items in self._menu_layout():
            menu = tk.Menu(mb, tearoff=0)
            self._fill_menu(menu, items)
            mb.add_cascade(label=title, menu=menu)
            self.submenus[title] = menu
        for cid in self.command_order:
            cmd = self.commands[cid]
            label = cmd["label"]
            if cmd["kind"] == "radio":
                group = cid.split(".")[0].capitalize()
                label = f"{group}: {label}"
            self.palette_items.append((f"{cmd['menu']}: {label}",
                                       lambda c=cid: self.run_command(c), self.accel(cid)))
        self._rebuild_recent()
        if not self.zen:
            self.root.config(menu=mb)

    def _build_context_menu(self):
        m = tk.Menu(self.root, tearoff=0)
        for item in ("edit.undo", "edit.redo", "-", "edit.cut", "edit.copy", "edit.paste",
                     "edit.paste_history", "-", "edit.select_all", "edit.comment", "bm.toggle",
                     "fold.toggle", "-", "search.definition", "help.doc", "edit.rename",
                     "insert.color"):
            if item == "-":
                m.add_separator()
            else:
                m.add_command(label=self.commands[item]["label"], accelerator=self.accel(item),
                              command=self.commands[item]["func"])
        self.context_menu = m
        t = tk.Menu(self.root, tearoff=0)
        self.tab_menu = t

    def _build_status_bar(self):
        bar = tk.Frame(self.root)
        self.status_bar = bar
        self.status = tk.Label(bar, anchor="w", padx=6, text="New file")
        self.status_items = {}
        for key in ("zoom", "eol", "enc", "indent", "lang", "counts", "pos", "branch", "goal",
                    "pomodoro", "macro", "vim"):
            label = tk.Label(bar, padx=6)
            label.pack(side="right")
            self.status_items[key] = label
        self.status.pack(side="left", fill="x", expand=True)
        bar.pack(side="bottom", fill="x")
        clicks = {"pos": self.goto_line, "counts": self.text_statistics,
                  "goal": self.set_word_goal, "pomodoro": self.toggle_pomodoro,
                  "zoom": self.reset_zoom, "macro": self.toggle_macro_recording,
                  "vim": lambda: None, "branch": self.show_git_status}
        for key, func in clicks.items():
            self.status_items[key].bind("<Button-1>", lambda e, f=func: f())
        menus = {"lang": "Language Mode", "enc": "Encoding", "eol": "Line Endings",
                 "indent": "Tab Width"}
        for key, name in menus.items():
            self.status_items[key].bind(
                "<Button-1>", lambda e, n=name: self.submenus[n].tk_popup(e.x_root, e.y_root))
        for label in self.status_items.values():
            label.config(cursor="hand2")

    def _build_main(self):
        self.style = ttk.Style(self.root)
        try:
            self.style.theme_use("clam")
        except tk.TclError:
            pass
        try:
            self.style.layout("Zen.TNotebook.Tab", [])
        except tk.TclError:
            pass
        self.tab_style = self._create_closable_tab_style()
        for orient in ("Vertical", "Horizontal"):
            for prefix in ("Editor", "Side"):
                try:
                    self.style.layout(f"{prefix}.{orient}.TScrollbar", [
                        (f"{orient}.Scrollbar.trough", {"sticky": "ns" if orient == "Vertical"
                                                        else "ew", "children": [
                            (f"{orient}.Scrollbar.thumb", {"expand": "1", "sticky": "nswe"})]})])
                except tk.TclError:
                    pass
        try:
            self.style.layout("Side.Treeview", [("Treeview.treearea", {"sticky": "nswe"})])
            self.style.layout("Panel.TNotebook", [("Panel.TNotebook.client", {"sticky": "nswe"})])
        except tk.TclError:
            pass
        self._build_activity_bar()
        self.hpane = tk.PanedWindow(self.root, orient="horizontal", bd=0, sashwidth=4)
        self.hpane.pack(fill="both", expand=True)
        self.main_pane = tk.PanedWindow(self.hpane, orient="vertical", bd=0, sashwidth=4)
        self.hpane.add(self.main_pane, stretch="always")
        self.nb = ttk.Notebook(self.main_pane, style=self.tab_style)
        self.main_pane.add(self.nb, stretch="always")
        self.nb.bind("<<NotebookTabChanged>>", self._on_tab_changed)
        if not self.aqua:
            self.nb.bind("<Button-2>", self._on_tab_middle_click)
        self.nb.bind("<Button-2>" if self.aqua else "<Button-3>", self._on_tab_right_click,
                     add="+")
        self.nb.bind("<ButtonPress-1>", self._on_tab_press)
        self.nb.bind("<B1-Motion>", self._on_tab_drag)
        self.nb.bind("<ButtonRelease-1>", self._on_tab_release)

    def _create_closable_tab_style(self):
        def x_image(color, size=14, gap=6):
            img = tk.PhotoImage(master=self.root, width=size + gap, height=size)
            for i in range(3, size - 3):
                for x, y in ((i, i), (i + 1, i), (size - 1 - i, i), (size - 2 - i, i)):
                    img.put(color, to=(gap + x, y))
            return img

        self._close_images = (x_image("#8A8A8A"), x_image("#E06C6C"), x_image("#B03A3A"))
        normal, hover, pressed = self._close_images
        try:
            if "close" not in self.style.element_names():
                self.style.element_create("close", "image", normal,
                                          ("active", "pressed", "!disabled", pressed),
                                          ("active", "!disabled", hover), sticky="")
            self.style.layout("Closable.TNotebook",
                              [("Closable.TNotebook.client", {"sticky": "nswe"})])
            self.style.layout("Closable.TNotebook.Tab", [
                ("Closable.TNotebook.tab", {"sticky": "nswe", "children": [
                    ("Closable.TNotebook.padding", {"side": "top", "sticky": "nswe", "children": [
                        ("Closable.TNotebook.label", {"side": "left", "sticky": ""}),
                        ("Closable.TNotebook.close", {"side": "left", "sticky": ""}),
                    ]}),
                ]}),
            ])
            return "Closable.TNotebook"
        except tk.TclError:
            return "TNotebook"

    def _build_output_panel(self):
        self.bottom_nb = ttk.Notebook(self.main_pane, style="Panel.TNotebook")
        f = tk.Frame(self.bottom_nb, bd=0)
        bar = tk.Frame(f, bd=0)
        bar.pack(fill="x")
        self.out_title = tk.Label(bar, text="", anchor="w", padx=6)
        self.out_title.pack(side="left")
        self.out_buttons = []
        for label, func in (("✕", self.hide_output), ("Clear", self.clear_output),
                            ("Stop", self.stop_run)):
            b = tk.Label(bar, text=label, padx=8, pady=1, cursor="hand2")
            b.bind("<Button-1>", lambda e, f=func: f())
            b.pack(side="right", padx=2, pady=2)
            self.out_buttons.append((b, label))
        body = tk.Frame(f, bd=0)
        body.pack(fill="both", expand=True)
        self.out_text = tk.Text(body, height=10, font=self.font, wrap="char", bd=0,
                                highlightthickness=0, padx=10, pady=4, state="disabled")
        sb = ttk.Scrollbar(body, command=self.out_text.yview, style="Editor.Vertical.TScrollbar")
        self.out_text.config(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self.out_text.pack(side="left", fill="both", expand=True)
        self.out_text.bind("<Double-Button-1>", self._output_jump)
        self.out_frame = f
        self.out_bar = bar
        self.out_body = body
        self.bottom_nb.add(f, text="OUTPUT")
        self.output_visible = False

    def _apply_chrome_theme(self):
        th = self.theme
        self.status_bar.config(bg=th["status_bg"])
        for w in [self.status] + list(self.status_items.values()):
            w.config(bg=th["status_bg"], fg=th["status_fg"])
        for text in (self.out_text, self.console_text):
            text.config(bg=th["bg"], fg=th["fg"], insertbackground=th["cursor"],
                        selectbackground=th["sel_bg"], selectforeground=th["sel_fg"],
                        inactiveselectbackground=th["sel_bg"])
            text.tag_configure("info", foreground=th["gutter_fg"])
            text.tag_configure("error", foreground=th["diff_del"])
            text.tag_configure("prompt", foreground=th["keyword"])
        for w in (self.out_bar, self.out_body, self.out_frame, self.console_frame):
            w.config(bg=th["bg"])
        self.out_title.config(bg=th["bg"], fg=th["tab_inactive_fg"])
        for b, _ in self.out_buttons:
            b.config(bg=th["bg"], fg=th["tab_inactive_fg"])
            b.bind("<Enter>", lambda e, w=b: w.config(bg=th["list_hover"]))
            b.bind("<Leave>", lambda e, w=b: w.config(bg=th["bg"]))
        bar_bg = th["side_bg"]
        self.find_bar.config(bg=bar_bg, highlightthickness=1, highlightbackground=th["border"])
        for w in self.find_bar.winfo_children():
            try:
                w.config(bg=bar_bg, fg=th["fg"], activebackground=th["list_hover"],
                         activeforeground=th["fg"], highlightthickness=0)
            except tk.TclError:
                try:
                    w.config(bg=bar_bg, fg=th["fg"])
                except tk.TclError:
                    pass
        try:
            self.find_entry_bar.config(bg=th["bg"], fg=th["fg"], insertbackground=th["cursor"],
                                       relief="flat", highlightthickness=1,
                                       highlightbackground=th["border"],
                                       highlightcolor=th["accent"])
            for cb in self.find_bar_checks:
                cb.config(selectcolor=th["bg"])
        except (AttributeError, tk.TclError):
            pass
        self.apply_ttk_theme()
        if hasattr(self, "side_panel"):
            self.apply_side_theme()
        else:
            self.refresh_activity_bar()

    def gutter_visible(self):
        return self.line_numbers.get() and not self.zen

    def tab_pixels(self):
        return max(1, self.font.measure(" " * self.tab_width.get()))

    def indent_unit(self, doc=None):
        doc = doc or self.current()
        if doc is None:
            return " " * self.tab_width.get() if self.use_spaces.get() else "\t"
        return " " * doc.indent_width if doc.indent_spaces else "\t"

    def save_config(self):
        if self._reset_pending:
            return
        self.cfg.update(
            font_family=self.font.cget("family"), font_size=self.font_size,
            wrap=self.wrap.get(), auto_indent=self.auto_indent.get(),
            line_numbers=self.line_numbers.get(), highlight=self.highlight.get(),
            theme=self.theme_var.get(), match_case=self.opt_case.get(),
            whole_word=self.opt_word.get(), regex=self.opt_regex.get(),
            tab_width=self.tab_width.get(), use_spaces=self.use_spaces.get(),
            auto_close=self.auto_close.get(), highlight_line=self.hl_line.get(),
            highlight_occurrences=self.hl_occ.get(), trim_on_save=self.trim_on_save.get(),
            restore_session=self.restore_session.get(), show_minimap=self.show_minimap.get(),
            show_guides=self.show_guides.get(), show_whitespace=self.show_ws.get(),
            show_trailing=self.show_trailing.get(), mark_long=self.mark_long.get(),
            show_ruler=self.show_ruler.get(), ruler_col=self.ruler_col.get(),
            rainbow=self.rainbow.get(), swatches=self.swatches.get(),
            typewriter=self.typewriter.get(), focus_mode=self.focus_mode.get(),
            auto_save=self.auto_save.get(), backup_bak=self.backup_bak.get(),
            detect_indent=self.detect_indent.get(), single_instance=self.single_instance.get(),
            vim_mode=self.vim_var.get(), explorer=self.explorer_var.get(),
            outline=self.outline_var.get(), ui_scale=self.ui_scale.get())
        try:
            write_json_file(CONFIG_FILE, self.cfg)
        except OSError:
            pass

    def _rebuild_recent(self):
        m = self.recent_menu
        m.delete(0, "end")
        recent = self.cfg.get("recent", [])
        if not recent:
            m.add_command(label="(empty)", state="disabled")
            return
        for i, path in enumerate(recent, 1):
            m.add_command(label=f"{i}. {path}", underline=0 if i < 10 else -1,
                          command=lambda p=path: self.open_file(p))
        m.add_separator()
        m.add_command(label="Clear List", command=self._clear_recent)

    def _add_recent(self, path):
        key = os.path.normcase(path)
        recent = [p for p in self.cfg.get("recent", []) if os.path.normcase(p) != key]
        self.cfg["recent"] = [path] + recent[:MAX_RECENT - 1]
        self._rebuild_recent()
        self.save_config()

    def _remove_recent(self, path):
        key = os.path.normcase(path)
        self.cfg["recent"] = [p for p in self.cfg.get("recent", []) if os.path.normcase(p) != key]
        self._rebuild_recent()
        self.save_config()

    def _clear_recent(self):
        self.cfg["recent"] = []
        self._rebuild_recent()
        self.save_config()

    def current(self):
        tab = self.nb.select()
        return self.docs.get(tab) if tab else None

    def cv(self):
        doc = self.current()
        return (doc, doc.view()) if doc else (None, None)

    def ordered_docs(self):
        return [self.docs[t] for t in self.nb.tabs() if t in self.docs]

    def new_tab(self, select=True):
        self._untitled += 1
        doc = Document(self, self._untitled)
        self.docs[str(doc.frame)] = doc
        self.nb.add(doc.frame, text=doc.name())
        if select:
            self.nb.select(doc.frame)
            doc.text.focus_set()
        return doc

    def close_tab(self, doc=None, force=False):
        doc = doc or self.current()
        if not doc:
            return False
        if doc.pinned and not force:
            self.set_message("This tab is pinned. Unpin it first (right-click the tab).")
            self.root.bell()
            return False
        self.nb.select(doc.frame)
        if doc.scratch:
            self.save_scratch(doc)
        elif not self._confirm_discard(doc):
            return False
        self._remove_recovery(doc)
        self.save_undo_history(doc)
        self.nb.forget(doc.frame)
        del self.docs[str(doc.frame)]
        doc.destroy()
        if not self.docs:
            self.new_tab()
        return True

    def close_other_tabs(self, keep=None):
        keep = keep or self.current()
        for doc in self.ordered_docs():
            if doc is not keep and not doc.pinned and not self.close_tab(doc):
                return
        if keep:
            self.nb.select(keep.frame)

    def close_all_tabs(self):
        for doc in self.ordered_docs():
            if not doc.pinned and not self.close_tab(doc):
                return

    def cycle_tab(self, step):
        tabs = self.nb.tabs()
        if len(tabs) > 1:
            i = tabs.index(self.nb.select())
            self.nb.select(tabs[(i + step) % len(tabs)])

    def update_tab(self, doc):
        mark = " \u25cf" if doc.modified() and not doc.scratch else ""
        lock = " [RO]" if doc.read_only and doc.kind == "text" else ""
        pin = "\u25c6 " if doc.pinned else ""
        try:
            self.nb.tab(doc.frame, text=f" {pin}{doc.name()}{lock}{mark}")
            if doc.tab_color:
                image = self._color_image(doc.tab_color)
            else:
                image = draw_icon(self.root, 16, file_icon_layers(doc.name()),
                                  self.theme["tab_inactive_bg"])
            self.nb.tab(doc.frame, image=image, compound="left")
        except tk.TclError:
            return
        if self.current() is doc:
            self.update_title()

    def update_title(self):
        doc = self.current()
        if doc:
            mark = "*" if doc.modified() else ""
            self.root.title(f"{mark}{doc.name()} - {APP}")

    def _on_tab_changed(self, event=None):
        doc = self.current()
        if not doc:
            return
        if self.auto_save.get():
            for other in self.docs.values():
                if other is not doc and other.modified() and (other.path or other.remote):
                    self.save(other, quiet=True)
        self.enc_var.set(doc.encoding)
        self.eol_var.set(EOL_NAMES[doc.eol])
        self.ro_var.set(doc.read_only)
        self.use_spaces.set(doc.indent_spaces)
        self.tab_width.set(doc.indent_width if doc.indent_width in (2, 4, 8) else 4)
        self.lang_var.set(doc.lang_override or "auto")
        self.update_title()
        self.update_status()
        self.set_message(doc.remote and doc.display_name or doc.path or "New file")
        doc.view().focus_set()
        doc.schedule_gutter()
        self.refresh_outline()
        self.explorer_reveal(doc)

    def _tab_at(self, event):
        try:
            idx = self.nb.index(f"@{event.x},{event.y}")
        except tk.TclError:
            return None
        if isinstance(idx, int) and 0 <= idx < len(self.nb.tabs()):
            return self.nb.tabs()[idx]
        return None

    def _on_tab_middle_click(self, event):
        tab = self._tab_at(event)
        if tab:
            self.close_tab(self.docs[tab])

    def _on_close_button(self, event):
        try:
            return "close" in self.nb.identify(event.x, event.y)
        except tk.TclError:
            return False

    def _on_tab_press(self, event):
        self._drag_tab = None
        if self._on_close_button(event):
            self._close_pressed = self._tab_at(event)
            if self._close_pressed:
                self.nb.state(["pressed"])
                return "break"
        self._drag_tab = self._tab_at(event)
        return None

    def _on_tab_release(self, event):
        tab, self._close_pressed = self._close_pressed, None
        self._drag_tab = None
        if not tab:
            return None
        self.nb.state(["!pressed"])
        if self._on_close_button(event) and self._tab_at(event) == tab and tab in self.docs:
            self.close_tab(self.docs[tab])
        return "break"

    def _on_tab_drag(self, event):
        if not self._drag_tab:
            return
        target = self._tab_at(event)
        if target and target != self._drag_tab:
            self.nb.insert(self.nb.tabs().index(target), self._drag_tab)

    def set_message(self, text):
        self.status.config(text=text)

    def update_status(self):
        doc, w = self.cv()
        items = self.status_items
        if not doc:
            return
        try:
            line, col = w.index("insert").split(".")
        except tk.TclError:
            return
        ch = w.get("insert")
        code_point = f"   U+{ord(ch):04X}" if ch and ch != "\n" else ""
        sel = w.tag_ranges("sel")
        if sel:
            s = w.get(sel[0], sel[1])
            counts = f"Sel: {len(s):,} chars, {len(s.split()):,} words"
        else:
            counts = f"{doc.words:,} words, {doc.chars:,} chars"
        position = f"Ln {line}, Col {int(col) + 1}{code_point}"
        if doc.read_only:
            position = "Read only   " + position
        items["pos"].config(text=position)
        items["counts"].config(text=counts)
        items["lang"].config(text=LANG_NAMES.get(doc.lang, "Plain Text") if doc.kind == "text"
                             else doc.kind.capitalize())
        items["indent"].config(text=f"Spaces: {doc.indent_width}" if doc.indent_spaces
                               else f"Tabs ({doc.indent_width})")
        items["enc"].config(text=doc.encoding)
        items["eol"].config(text=EOL_NAMES[doc.eol] + (" (mixed)" if doc.mixed_eol else ""))
        items["zoom"].config(text=f"{self.font_size}pt")
        items["branch"].config(text=f"⎇ {doc.git_branch}" if doc.git_branch else "")
        if doc.word_goal:
            pct = min(100, doc.words * 100 // max(1, doc.word_goal))
            items["goal"].config(text=f"Goal: {doc.words:,}/{doc.word_goal:,} ({pct}%)")
        else:
            items["goal"].config(text="")
        items["macro"].config(text="● REC" if self.macro_recording else "")
        if self.vim_var.get() and doc.kind == "text":
            mode = {"normal": "NORMAL", "insert": "INSERT", "visual": "VISUAL",
                    "vline": "VISUAL LINE"}.get(doc.vim_mode, "")
            items["vim"].config(text=f"-- {mode} --")
        else:
            items["vim"].config(text="")
        self.layout_status()

    def _read(self, path, encoding=None):
        try:
            with open(path, "rb") as f:
                data = f.read()
        except OSError as e:
            messagebox.showerror("Error", "Could not open file:\n{error}".format(error=e))
            return None
        content, enc = decode_bytes(data, encoding)
        return content, enc, len(data), looks_binary(data)

    def _find_open(self, path):
        if not path:
            return None
        key = os.path.normcase(os.path.abspath(path))
        for doc in self.docs.values():
            if doc.path and os.path.normcase(doc.path) == key:
                return doc
        return None

    def open_file(self, path=None, read_only=False, line=None, col=0):
        if not path:
            paths = filedialog.askopenfilenames(title="Open File", filetypes=self._filetypes())
            if isinstance(paths, str):
                paths = self.root.tk.splitlist(paths)
            doc = None
            for p in paths:
                doc = self.open_file(p) or doc
            return doc
        path = os.path.abspath(path)
        existing = self._find_open(path)
        if existing:
            self.nb.select(existing.frame)
            if line:
                self._goto(existing, line, col)
            return existing
        ext = os.path.splitext(path)[1].lower()
        if ext in (".png", ".gif", ".ppm", ".pgm"):
            return self.open_image(path)
        if ext == ".zip" and zipfile.is_zipfile(path):
            self.open_archive(path)
            return None
        try:
            size = os.path.getsize(path)
        except OSError:
            size = 0
        if size > LARGE_FILE:
            answer = messagebox.askyesnocancel(
                APP, f"{os.path.basename(path)} is {size / 1048576:.0f} MB.\n\n"
                     "Yes: open it in the large file viewer (read-only, loads as you scroll).\n"
                     "No: load the whole file (may be slow).")
            if answer is None:
                return None
            if answer:
                return self.open_lazy(path, "text")
        result = self._read(path)
        if result is None:
            self._remove_recent(path)
            return None
        content, enc, size, binary = result
        if binary:
            answer = messagebox.askyesnocancel(
                APP, f"{os.path.basename(path)} looks like a binary file.\n\n"
                     "Yes: open it in the hex viewer.\nNo: open it as text (read-only).")
            if answer is None:
                return None
            if answer:
                return self.open_lazy(path, "hex")
            read_only = True
        cur = self.current()
        doc = cur if cur and cur.is_blank() else self.new_tab()
        if read_only:
            doc.set_read_only(True)
        doc.load(path, content, enc, size)
        self.load_undo_history(doc)
        self.git_refresh(doc)
        self._on_tab_changed()
        self._add_recent(path)
        if line:
            self._goto(doc, line, col)
        return doc

    def _filetypes(self):
        return [("All files", "*.*"),
                ("Text files", "*.txt *.md *.py *.csv *.json *.log *.ini *.xml *.html *.yml")]

    def reload(self, doc=None, encoding=None, ask=True):
        doc = doc or self.current()
        if not doc or not doc.path:
            self.set_message("This document has not been saved to disk")
            return
        if doc.kind == "image":
            self.load_image(doc, doc.path)
            return
        if doc.kind != "text":
            self.set_message("Reopen the file to reload this view")
            return
        if ask and doc.modified() and not messagebox.askyesno(
                APP, f"Discard unsaved changes to {doc.name()} and reload from disk?"):
            return
        result = self._read(doc.path, encoding)
        if result:
            lines = doc.bookmark_lines()
            cursor = doc.text.index("insert")
            doc.load(doc.path, *result[:3])
            doc.set_bookmark_lines(lines)
            try:
                doc.text.mark_set("insert", cursor)
                doc.text.see("insert")
            except tk.TclError:
                pass
            self._remove_recovery(doc)
            self.git_refresh(doc)
            self._on_tab_changed()

    def save(self, doc=None, quiet=False):
        doc = doc or self.current()
        if not doc:
            return False
        if doc.kind != "text":
            self.set_message("This view cannot be saved")
            return False
        if doc.scratch:
            self.save_scratch(doc)
            return True
        if doc.remote:
            return self.save_ftp(doc)
        if not doc.path:
            return False if quiet else self.save_as(doc)
        return self._write(doc, doc.path)

    def save_as(self, doc=None):
        doc = doc or self.current()
        if not doc or doc.kind != "text":
            return False
        name = (doc.name() if (doc.path or doc.display_name)
                else "Untitled" + getattr(doc, "default_ext", ".txt"))
        name = re.sub(r'[\\/:*?"<>|]', "_", name)
        path = filedialog.asksaveasfilename(
            title="Save As", defaultextension=os.path.splitext(name)[1] or ".txt",
            initialfile=name, initialdir=os.path.dirname(doc.path) if doc.path else None,
            filetypes=self._filetypes())
        if not path:
            return False
        doc.remote = None
        doc.display_name = None
        doc.scratch = False
        return self._write(doc, path)

    def save_all(self):
        saved = 0
        current = self.current()
        for doc in self.ordered_docs():
            if doc.modified():
                self.nb.select(doc.frame)
                if not self.save(doc):
                    return
                saved += 1
        if current:
            self.nb.select(current.frame)
        self.set_message("Saved {count} file(s)".format(count=saved))

    def _write(self, doc, path):
        if self.trim_on_save.get() and not doc.read_only:
            content = doc.content()
            trimmed = re.sub(r"[ \t]+$", "", content, flags=re.MULTILINE)
            if trimmed != content:
                self.edit_block(doc, doc.text, "1.0", "end-1c", trimmed)
        content = doc.content()
        data_text = content.replace("\n", doc.eol) if doc.eol != "\n" else content
        try:
            data = data_text.encode(doc.encoding)
        except UnicodeEncodeError as e:
            messagebox.showerror(
                "Error", f"The text contains characters that {doc.encoding} cannot store:\n{e}"
                         "\n\nChoose UTF-8 in the Encoding menu and save again.")
            return False
        try:
            if self.backup_bak.get() and os.path.isfile(path):
                shutil.copy2(path, path + ".bak")
            with open(path, "wb") as f:
                f.write(data)
        except OSError as e:
            messagebox.showerror("Error", f"Could not save file:\n{e}")
            return False
        doc.path = os.path.abspath(path)
        doc.mixed_eol = False
        try:
            doc.mtime = os.path.getmtime(doc.path)
        except OSError:
            doc.mtime = None
        doc.text.edit_modified(False)
        doc.setup_language()
        self.update_tab(doc)
        self._remove_recovery(doc)
        self._add_recent(doc.path)
        self.add_history_version(doc.path, content)
        self.set_message(f"Saved: {doc.path}")
        self.check_syntax(doc, quiet=True)
        self.git_refresh(doc)
        norm = os.path.normcase(doc.path)
        if norm == os.path.normcase(os.path.abspath(SNIPPETS_FILE)):
            self.snippets = self.load_snippets()
        elif norm == os.path.normcase(os.path.abspath(KEYBINDINGS_FILE)):
            self.rebind_shortcuts()
            self.set_message("Keybindings reloaded")
        elif norm == os.path.normcase(os.path.abspath(THEMES_FILE)):
            self.load_user_themes()
            self._build_commands()
            self._build_menu()
            self.set_theme()
            self.set_message("Themes reloaded")
        return True

    def _confirm_discard(self, doc):
        if not doc.modified() or doc.scratch:
            return True
        answer = messagebox.askyesnocancel(APP, f"Save changes to {doc.name()}?")
        if answer is None:
            return False
        if answer:
            return self.save(doc)
        return True

    def set_encoding(self):
        doc = self.current()
        if doc:
            doc.encoding = self.enc_var.get()
            self.update_status()
            self.set_message("Encoding set to {enc}; it will be used on next save".format(
                enc=doc.encoding))

    def set_eol(self):
        doc = self.current()
        if doc:
            doc.eol = EOLS[self.eol_var.get()]
            self.update_status()
            self.set_message("Line endings set to {eol}; they will be used on next save"
                             .format(eol=self.eol_var.get()))

    def print_file(self):
        doc = self.current()
        if not doc:
            return
        content = doc.content()
        if not content.strip():
            self.set_message("Nothing to print")
            return
        win = tk.Toplevel(self.root)
        win.title("Print")
        win.transient(self.root)
        win.resizable(False, False)
        numbers = tk.BooleanVar(value=True)
        header = tk.BooleanVar(value=True)
        tk.Label(win, text=f"Print {doc.name()} to the default printer.").pack(padx=12,
                                                                               pady=(12, 6))
        tk.Checkbutton(win, text="Line numbers", variable=numbers).pack(anchor="w", padx=12)
        tk.Checkbutton(win, text="Header with file name, page and date",
                       variable=header).pack(anchor="w", padx=12)

        def go():
            win.destroy()
            self._print(doc, content, numbers.get(), header.get())

        buttons = tk.Frame(win)
        buttons.pack(pady=10)
        tk.Button(buttons, text="Print", width=10, command=go).pack(side="left", padx=4)
        tk.Button(buttons, text="Cancel", width=10, command=win.destroy).pack(side="left",
                                                                              padx=4)
        win.bind("<Escape>", lambda e: win.destroy())

    def _save_session(self):
        files = []
        for doc in self.ordered_docs():
            if doc.path and os.path.isfile(doc.path) and doc.kind in ("text", "image"):
                files.append({"path": doc.path, "cursor": doc.text.index("insert"),
                              "top": doc.text.index("@0,0"), "read_only": doc.read_only,
                              "bookmarks": doc.bookmark_lines(), "pinned": doc.pinned,
                              "color": doc.tab_color, "scratch": doc.scratch,
                              "lang": doc.lang_override, "goal": doc.word_goal})
        cur = self.current()
        self.cfg["session"] = {"files": files, "current": cur.path if cur else None}

    def _restore_session(self):
        if not self.restore_session.get():
            return
        session = self.cfg.get("session") or {}
        for item in session.get("files", []):
            path = item.get("path")
            if not path or not os.path.isfile(path):
                continue
            if item.get("scratch"):
                doc = self.open_scratchpad()
            else:
                doc = self.open_file(path, read_only=item.get("read_only", False))
            if not doc:
                continue
            try:
                doc.pinned = bool(item.get("pinned"))
                doc.tab_color = item.get("color")
                doc.word_goal = int(item.get("goal") or 0)
                if item.get("lang"):
                    doc.lang_override = item["lang"]
                    doc.setup_language()
                doc.set_bookmark_lines(item.get("bookmarks", []))
                doc.text.mark_set("insert", item.get("cursor", "1.0"))
                doc.text.yview(item.get("top", "1.0"))
                self.update_tab(doc)
            except (tk.TclError, ValueError):
                pass
        doc = self._find_open(session.get("current"))
        if doc:
            self.nb.select(doc.frame)

    def _recovery_path(self, doc):
        return os.path.join(RECOVERY_DIR, doc.id + ".json")

    def _remove_recovery(self, doc):
        try:
            os.remove(self._recovery_path(doc))
        except OSError:
            pass

    def _write_recovery(self):
        try:
            os.makedirs(RECOVERY_DIR, exist_ok=True)
            for doc in self.docs.values():
                if doc.modified():
                    data = {"path": doc.path, "encoding": doc.encoding,
                            "eol": EOL_NAMES[doc.eol], "content": doc.content()}
                    with open(self._recovery_path(doc), "w", encoding="utf-8") as f:
                        json.dump(data, f)
                else:
                    self._remove_recovery(doc)
        except OSError:
            pass

    def _recovery_tick(self):
        self._write_recovery()
        self.root.after(RECOVERY_INTERVAL, self._recovery_tick)

    def _recover(self):
        try:
            files = [os.path.join(RECOVERY_DIR, f) for f in os.listdir(RECOVERY_DIR)
                     if f.endswith(".json")]
        except OSError:
            return
        if not files:
            return
        if messagebox.askyesno(APP, ("Found {count} unsaved document(s) from a previous "
                                       "session.\nDo you want to restore them?").format(
                count=len(files))):
            for path in files:
                try:
                    with open(path, encoding="utf-8") as f:
                        data = json.load(f)
                except (OSError, ValueError):
                    continue
                doc = self._find_open(data.get("path"))
                if doc is None:
                    cur = self.current()
                    doc = cur if cur and cur.is_blank() else self.new_tab()
                doc.set_read_only(False)
                doc.set_content(data.get("content", ""))
                doc.path = data.get("path")
                doc.encoding = data.get("encoding") or "utf-8"
                doc.eol = EOLS.get(data.get("eol"), DEFAULT_EOL)
                try:
                    doc.mtime = os.path.getmtime(doc.path) if doc.path else None
                except OSError:
                    doc.mtime = None
                doc.text.edit_modified(True)
                doc.setup_language()
                self.update_tab(doc)
        for path in files:
            try:
                os.remove(path)
            except OSError:
                pass

    def _disk_tick(self):
        if not self._checking:
            self._checking = True
            try:
                self._check_disk()
            finally:
                self._checking = False
        self.root.after(DISK_CHECK_INTERVAL, self._disk_tick)

    def _check_disk(self):
        for doc in list(self.docs.values()):
            if (not doc.path or doc.mtime is None or doc.follow or doc.lazy or doc.scratch
                    or doc.remote):
                continue
            try:
                mtime = os.path.getmtime(doc.path)
            except OSError:
                doc.mtime = None
                self.nb.select(doc.frame)
                messagebox.showwarning(APP, f"{doc.path}\n\nwas deleted or moved. "
                                            "Save it to keep its contents.")
                if doc.kind == "text":
                    doc.text.edit_modified(True)
                continue
            if mtime == doc.mtime:
                continue
            doc.mtime = mtime
            self.nb.select(doc.frame)
            if doc.modified():
                msg = (f"{doc.path}\n\nwas changed by another program and you have unsaved "
                       "changes.\nReload it and lose your changes?")
            else:
                msg = f"{doc.path}\n\nwas changed by another program. Reload it?"
            if messagebox.askyesno(APP, msg):
                self.reload(doc, ask=False)

    def _editable(self, doc):
        if doc is None:
            return False
        if doc.read_only:
            self.set_message("This document is read-only")
            self.root.bell()
            return False
        return True

    def _text_event(self, name):
        doc, w = self.cv()
        if doc:
            w.focus_set()
            w.event_generate(name)

    def select_all(self):
        doc, w = self.cv()
        if doc:
            w.tag_add("sel", "1.0", "end-1c")
            self.update_status()

    def insert_datetime(self):
        doc, w = self.cv()
        if self._editable(doc):
            w.insert("insert", time.strftime("%H:%M %d/%m/%Y"))

    def _goto(self, doc, line, col=0, view=None, record=True):
        w = view or doc.view()
        if record:
            self.push_nav(doc, w.index("insert"))
        if doc.frame and self.current() is not doc:
            self.nb.select(doc.frame)
        doc.reveal(f"{line}.{col}")
        w.tag_remove("sel", "1.0", "end")
        w.mark_set("insert", f"{line}.{col}")
        w.see("insert")
        w.focus_set()

    def goto_line(self):
        doc, w = self.cv()
        if not doc:
            return
        last = int(w.index("end-1c").split(".")[0])
        line = simpledialog.askinteger("Go To Line", "Line number (1-{last}):".format(
            last=last), parent=self.root, minvalue=1, maxvalue=last)
        if line:
            self._goto(doc, line)

    def show_context_menu(self, event):
        event.widget.focus_set()
        try:
            self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()

    def toggle_read_only(self):
        doc = self.current()
        if doc:
            doc.set_read_only(self.ro_var.get())
            self.update_status()

    def edit_block(self, doc, w, start, end, new, select=False, keep_cursor=True):
        start, end = w.index(start), w.index(end)
        cursor = w.index("insert")
        whole = start == "1.0" and w.compare(end, ">=", "end-1c")
        marks = doc.bookmark_lines() if whole else None
        w.config(autoseparators=False)
        try:
            w.edit_separator()
            w.delete(start, end)
            w.insert(start, new)
            w.edit_separator()
        finally:
            w.config(autoseparators=True)
        if marks is not None:
            doc.set_bookmark_lines(marks)
        w.tag_remove("sel", "1.0", "end")
        if select:
            w.tag_add("sel", start, f"{start}+{len(new)}c")
        if keep_cursor:
            w.mark_set("insert", cursor)
        w.see("insert")

    def indent_lines(self, doc, w, dedent):
        if not self._editable(doc):
            return
        had_sel = bool(w.tag_ranges("sel"))
        first, last = selected_lines(w)
        width = doc.indent_width
        unit = self.indent_unit(doc)
        cursor = w.index("insert")
        w.config(autoseparators=False)
        try:
            w.edit_separator()
            for ln in range(first, last + 1):
                line = w.get(f"{ln}.0", f"{ln}.end")
                if dedent:
                    m = re.match(r"\t| {1,%d}" % width, line)
                    if m:
                        w.delete(f"{ln}.0", f"{ln}.{len(m.group())}")
                elif line.strip() or first == last:
                    w.insert(f"{ln}.0", unit)
            w.edit_separator()
        finally:
            w.config(autoseparators=True)
        if had_sel:
            w.tag_add("sel", f"{first}.0", f"{last}.end")
        elif not dedent:
            w.mark_set("insert", f"{cursor}+{len(unit)}c")

    def indent_cmd(self, dedent):
        doc, w = self.cv()
        if doc:
            self.indent_lines(doc, w, dedent)

    def toggle_comment(self):
        doc, w = self.cv()
        if not self._editable(doc):
            return
        style = COMMENT_STYLES.get(doc.lang)
        if not style:
            self.set_message("This file type does not support comments")
            self.root.bell()
            return
        prefix, suffix = style
        had_sel = bool(w.tag_ranges("sel"))
        first, last = selected_lines(w)
        lines = [w.get(f"{ln}.0", f"{ln}.end") for ln in range(first, last + 1)]
        filled = [l for l in lines if l.strip()]
        if not filled:
            return

        def commented(line):
            s = line.strip()
            ok = s.lower().startswith(prefix.lower())
            return ok and (not suffix or s.endswith(suffix))

        new = []
        if all(commented(l) for l in filled):
            for line in lines:
                if not line.strip():
                    new.append(line)
                    continue
                body = line.lstrip()
                indent = line[:len(line) - len(body)]
                body = body[len(prefix):]
                if body.startswith(" "):
                    body = body[1:]
                if suffix:
                    body = body.rstrip()[:-len(suffix)]
                    if body.endswith(" "):
                        body = body[:-1]
                new.append(indent + body)
        else:
            col = min(len(l) - len(l.lstrip()) for l in filled)
            for line in lines:
                if line.strip():
                    line = line[:col] + prefix + " " + line[col:] + (" " + suffix if suffix else "")
                new.append(line)
        self.edit_block(doc, w, f"{first}.0", f"{last}.end", "\n".join(new), select=had_sel)
        if not had_sel:
            w.mark_set("insert", f"{first}.end")

    def duplicate_line(self):
        doc, w = self.cv()
        if not self._editable(doc):
            return
        if w.tag_ranges("sel"):
            start, end = w.index("sel.first"), w.index("sel.last")
            text = w.get(start, end)
            w.insert(end, text)
            w.tag_remove("sel", "1.0", "end")
            w.tag_add("sel", end, f"{end}+{len(text)}c")
            return
        line, col = map(int, w.index("insert").split("."))
        text = w.get(f"{line}.0", f"{line}.end")
        w.insert(f"{line}.end", "\n" + text)
        w.mark_set("insert", f"{line + 1}.{col}")
        w.see("insert")

    def move_lines(self, delta):
        doc, w = self.cv()
        if not self._editable(doc):
            return
        first, last = selected_lines(w)
        total = int(w.index("end-1c").split(".")[0])
        if (delta < 0 and first == 1) or (delta > 0 and last == total):
            return
        had_sel = bool(w.tag_ranges("sel"))
        line, col = map(int, w.index("insert").split("."))
        block = w.get(f"{first}.0", f"{last}.end")
        if delta < 0:
            other = w.get(f"{first - 1}.0", f"{first - 1}.end")
            start, end, new = f"{first - 1}.0", f"{last}.end", block + "\n" + other
        else:
            other = w.get(f"{last + 1}.0", f"{last + 1}.end")
            start, end, new = f"{first}.0", f"{last + 1}.end", other + "\n" + block
        self.edit_block(doc, w, start, end, new, keep_cursor=False)
        if had_sel:
            w.tag_add("sel", f"{first + delta}.0", f"{last + delta}.end")
        w.mark_set("insert", f"{line + delta}.{col}")
        w.see("insert")

    def delete_line(self):
        doc, w = self.cv()
        if not self._editable(doc):
            return
        first, last = selected_lines(w)
        total = int(w.index("end-1c").split(".")[0])
        if last < total:
            start, end = f"{first}.0", f"{last + 1}.0"
        elif first > 1:
            start, end = f"{first - 1}.end", f"{last}.end"
        else:
            start, end = "1.0", "end-1c"
        self.edit_block(doc, w, start, end, "", keep_cursor=False)
        w.mark_set("insert", f"{min(first, int(w.index('end-1c').split('.')[0]))}.0")
        w.see("insert")

    def autocomplete(self):
        doc, w = self.cv()
        if not self._editable(doc):
            return
        m = re.search(r"\w+$", w.get("insert linestart", "insert"))
        if not m:
            self.root.bell()
            return
        prefix = m.group()
        candidates = set()
        for other in self.docs.values():
            if other.kind == "text":
                text = other.content()
                if len(text) <= HIGHLIGHT_LIMIT:
                    candidates.update(re.findall(r"\w{3,}", text))
        if doc.lang == "python":
            candidates.update(PY_KEYWORDS.split() + PY_BUILTINS.split())
        words = sorted((c for c in candidates if c.startswith(prefix) and c != prefix),
                       key=lambda c: (c.lower(), c))[:200]
        if not words:
            self.set_message("No suggestions")
            self.root.bell()
            return
        if len(words) == 1:
            w.insert("insert", words[0][len(prefix):])
            return
        self._completion_popup(w, prefix, words)

    def _completion_popup(self, w, prefix, words):
        bbox = w.bbox("insert")
        if not bbox:
            return
        popup = tk.Toplevel(self.root)
        popup.overrideredirect(True)
        x = w.winfo_rootx() + bbox[0]
        y = w.winfo_rooty() + bbox[1] + bbox[3]
        popup.geometry(f"+{x}+{y}")
        th = self.theme
        lb = tk.Listbox(popup, height=min(10, len(words)), font=self.font, activestyle="none",
                        bg=th["bg"], fg=th["fg"], selectbackground=th["sel_bg"],
                        selectforeground=th["sel_fg"], highlightthickness=1, bd=0,
                        width=max(len(x) for x in words) + 2)
        lb.pack()
        for word in words:
            lb.insert("end", word)
        lb.selection_set(0)
        lb.activate(0)

        def close(event=None):
            popup.destroy()
            w.focus_set()

        def choose(event=None):
            sel = lb.curselection()
            if sel:
                w.insert("insert", lb.get(sel[0])[len(prefix):])
            close()
            return "break"

        lb.bind("<Return>", choose)
        lb.bind("<Tab>", choose)
        lb.bind("<Double-Button-1>", choose)
        lb.bind("<Escape>", close)
        lb.bind("<FocusOut>", close)
        popup.after(10, lb.focus_set)

    def load_snippets(self, quiet=False):
        snippets = {lang: dict(items) for lang, items in DEFAULT_SNIPPETS.items()}
        try:
            with open(SNIPPETS_FILE, encoding="utf-8") as f:
                user = json.load(f)
        except OSError:
            return snippets
        except ValueError as e:
            if not quiet:
                messagebox.showerror("Error", "snippets.json is not valid JSON:\n{error}"
                                     .format(error=e))
            return snippets
        if isinstance(user, dict):
            for lang, items in user.items():
                if isinstance(items, dict):
                    snippets[lang] = {k: v for k, v in items.items() if isinstance(v, str)}
        if not quiet:
            self.set_message("Snippets reloaded")
        return snippets

    def edit_snippets(self):
        if not os.path.exists(SNIPPETS_FILE):
            try:
                os.makedirs(CONFIG_DIR, exist_ok=True)
                with open(SNIPPETS_FILE, "w", encoding="utf-8") as f:
                    json.dump(DEFAULT_SNIPPETS, f, indent=2, ensure_ascii=False)
            except OSError as e:
                messagebox.showerror("Error", "Could not save file:\n{error}".format(
                    error=e))
                return
        self.open_file(SNIPPETS_FILE)
        self.set_message(("Edit the snippets and save the file to apply them. "
                            "Type a name and press Tab to expand it; $0 marks the cursor."))

    def expand_snippet(self, doc, w):
        before = w.get("insert linestart", "insert")
        m = re.search(r"(\w+)$", before)
        if not m:
            return False
        key = m.group(1)
        body = self.snippets.get(doc.lang or "text", {}).get(key)
        if body is None:
            body = self.snippets.get("*", {}).get(key)
        if body is None:
            return False
        unit = self.indent_unit(doc)
        body = re.sub(r"(?m)^((?:    )+)", lambda x: unit * (len(x.group(1)) // 4), body)
        indent = re.match(r"[ \t]*", before).group()
        lines = body.split("\n")
        body = lines[0] + "".join("\n" + indent + line for line in lines[1:])
        start = w.index(f"insert-{len(key)}c")
        self.insert_snippet(doc, w, start, "insert", body)
        return True

    def toggle_bookmark(self):
        doc, w = self.cv()
        if doc:
            line = int(w.index("insert").split(".")[0])
            added = doc.toggle_bookmark(line)
            self.set_message(("Bookmark added on line {line}" if added
                              else "Bookmark removed from line {line}").format(line=line))

    def goto_bookmark(self, step):
        doc, w = self.cv()
        if not doc:
            return
        lines = doc.bookmark_lines()
        if not lines:
            self.set_message("No bookmarks (Ctrl+F2 adds one)")
            self.root.bell()
            return
        cur = int(w.index("insert").split(".")[0])
        if step > 0:
            target = next((ln for ln in lines if ln > cur), lines[0])
        else:
            target = next((ln for ln in reversed(lines) if ln < cur), lines[-1])
        self._goto(doc, target, view=w)

    def clear_bookmarks(self):
        doc = self.current()
        if doc:
            doc.clear_bookmarks()

    def _target_range(self, w, fallback):
        if w.tag_ranges("sel"):
            if fallback == "lines":
                first, last = selected_lines(w)
                return f"{first}.0", w.index(f"{last}.end"), True
            return w.index("sel.first"), w.index("sel.last"), True
        if fallback == "word":
            line, col = map(int, w.index("insert").split("."))
            text = w.get(f"{line}.0", f"{line}.end")
            for m in re.finditer(r"\w+", text):
                if m.start() <= col <= m.end():
                    return f"{line}.{m.start()}", f"{line}.{m.end()}", False
            return None
        if fallback == "line":
            return w.index("insert linestart"), w.index("insert lineend"), False
        return "1.0", w.index("end-1c"), False

    def _transform(self, func, fallback="text", success=None):
        doc, w = self.cv()
        if not self._editable(doc):
            return
        target = self._target_range(w, fallback)
        if not target:
            self.root.bell()
            return
        start, end, has_sel = target
        old = w.get(start, end)
        try:
            new = func(old)
        except ToolError as e:
            if e.line:
                self._goto(doc, int(start.split(".")[0]) + e.line - 1, view=w)
            messagebox.showerror(APP, str(e))
            return
        if new == old:
            self.set_message("No changes")
            return
        self.edit_block(doc, w, start, end, new, select=has_sel)
        if success:
            self.set_message(success)

    def change_case(self, kind):
        funcs = {"upper": str.upper, "lower": str.lower,
                 "title": lambda s: re.sub(r"\w+", lambda m: m.group().capitalize(), s)}
        self._transform(funcs[kind], "word")

    def sort_lines(self):
        self._transform(lambda s: "\n".join(sorted(s.split("\n"), key=str.lower)), "lines",
                        "Lines sorted")

    def unique_lines(self):
        def unique(s):
            lines = s.split("\n")
            result = list(dict.fromkeys(lines))
            self.set_message("Removed {count} duplicate line(s)".format(
                count=len(lines) - len(result)))
            return "\n".join(result)
        self._transform(unique, "lines")

    def trim_trailing(self):
        self._transform(lambda s: re.sub(r"[ \t]+$", "", s, flags=re.MULTILINE), "lines",
                        "Trailing spaces removed")

    def format_json(self, minify):
        def fmt(s):
            try:
                data = json.loads(s)
            except json.JSONDecodeError as e:
                raise ToolError("Invalid JSON: {error} (line {line}, column {col})".format(
                    error=e.msg, line=e.lineno, col=e.colno), e.lineno)
            if minify:
                return json.dumps(data, ensure_ascii=False, separators=(",", ":"))
            indent = self.tab_width.get() if self.use_spaces.get() else "\t"
            return json.dumps(data, ensure_ascii=False, indent=indent)
        self._transform(fmt, "text", "JSON is valid")

    def format_xml(self):
        def fmt(s):
            try:
                dom = xml.dom.minidom.parseString(s.encode("utf-8"))
            except ExpatError as e:
                raise ToolError("Invalid XML: {error}".format(error=e), e.lineno)
            pretty = dom.toprettyxml(indent=self.indent_unit())
            lines = [line for line in pretty.split("\n") if line.strip()]
            stripped = s.lstrip()
            if stripped.startswith("<?xml"):
                lines[0] = stripped[:stripped.index("?>") + 2]
            else:
                lines = lines[1:]
            return "\n".join(lines)
        self._transform(fmt, "text", "XML is valid")

    def codec_tool(self, kind):
        def b64decode(s):
            data = "".join(s.split())
            data += "=" * (-len(data) % 4)
            try:
                if "-" in data or "_" in data:
                    raw = base64.urlsafe_b64decode(data)
                else:
                    raw = base64.b64decode(data, validate=True)
            except (ValueError, binascii.Error):
                raise ToolError("The text is not valid Base64.")
            try:
                return raw.decode("utf-8")
            except UnicodeDecodeError:
                raise ToolError("The decoded data is not text.")

        funcs = {
            "b64e": lambda s: base64.b64encode(s.encode("utf-8")).decode("ascii"),
            "b64d": b64decode,
            "urle": lambda s: urllib.parse.quote(s, safe=""),
            "urld": urllib.parse.unquote,
        }
        self._transform(funcs[kind], "text")

    def show_hash(self, algo):
        doc, w = self.cv()
        if not doc:
            return
        start, end, has_sel = self._target_range(w, "text")
        data = w.get(start, end).encode("utf-8")
        digest = hashlib.new(algo.replace("-", "").lower(), data).hexdigest()
        self.root.clipboard_clear()
        self.root.clipboard_append(digest)
        scope = "selection" if has_sel else "document"
        messagebox.showinfo(APP, f"{algo} ({scope}):\n\n{digest}\n\n"
                            + "Copied to the clipboard.")

    def calculate(self):
        doc, w = self.cv()
        if not self._editable(doc):
            return
        has_sel = bool(w.tag_ranges("sel"))
        if has_sel:
            start, end = w.index("sel.first"), w.index("sel.last")
        else:
            start, end = w.index("insert linestart"), w.index("insert lineend")
        text = w.get(start, end)
        stripped = text.rstrip()
        ends_eq = stripped.endswith("=")
        expression = stripped[:-1] if ends_eq else stripped
        if not has_sel and "=" in expression:
            expression = expression.rsplit("=", 1)[1]
        try:
            result = format_number(safe_eval(expression))
        except (ValueError, SyntaxError, ZeroDivisionError, OverflowError, TypeError) as e:
            self.set_message("Cannot calculate: {error}".format(error=e))
            self.root.bell()
            return
        if has_sel:
            self.edit_block(doc, w, start, end, result, select=True)
        else:
            new = stripped + (" " if ends_eq else " = ") + result
            self.edit_block(doc, w, start, end, new, keep_cursor=False)
            w.mark_set("insert", f"{start} lineend")
        self.set_message("Result: {value}".format(value=result))

    def compare_with(self):
        doc = self.current()
        if not doc:
            return
        others = [d for d in self.ordered_docs() if d is not doc]
        win = tk.Toplevel(self.root)
        win.title("Compare With...")
        win.transient(self.root)
        win.resizable(False, False)
        tk.Label(win, text="Compare {name} with:".format(name=doc.name()),
                 anchor="w").pack(fill="x", padx=8, pady=(8, 4))
        lb = tk.Listbox(win, height=8, width=50, exportselection=False)
        lb.pack(padx=8)
        for d in others:
            lb.insert("end", d.path or d.name())
        if others:
            lb.selection_set(0)

        def with_tab(event=None):
            sel = lb.curselection()
            if not sel:
                return
            other = others[sel[0]]
            win.destroy()
            self._show_diff(doc.path or doc.name(), doc.content(),
                            other.path or other.name(), other.content())

        def with_file():
            path = filedialog.askopenfilename(parent=win, title="Open File",
                                              filetypes=self._filetypes())
            if not path:
                return
            result = self._read(path)
            if result is None:
                return
            win.destroy()
            text = result[0].replace("\r\n", "\n").replace("\r", "\n")
            self._show_diff(doc.path or doc.name(), doc.content(), path, text)

        lb.bind("<Double-Button-1>", with_tab)
        buttons = tk.Frame(win)
        buttons.pack(pady=8)
        tk.Button(buttons, text="Compare", width=12, command=with_tab,
                  state="normal" if others else "disabled").pack(side="left", padx=4)
        tk.Button(buttons, text="Other File...", width=12,
                  command=with_file).pack(side="left", padx=4)
        tk.Button(buttons, text="Cancel", width=12, command=win.destroy).pack(side="left",
                                                                                  padx=4)
        win.bind("<Escape>", lambda e: win.destroy())

    def _show_diff(self, a_name, a_text, b_name, b_text):
        lines = list(difflib.unified_diff(a_text.split("\n"), b_text.split("\n"),
                                          a_name, b_name, lineterm=""))
        if not lines:
            messagebox.showinfo(APP, "The files are identical.")
            return
        added = sum(1 for l in lines if l.startswith("+") and not l.startswith("+++"))
        removed = sum(1 for l in lines if l.startswith("-") and not l.startswith("---"))
        win = tk.Toplevel(self.root)
        win.title("Differences" + f"  (+{added}  −{removed})")
        win.geometry("900x560")
        th = self.theme
        text = tk.Text(win, font=self.font, wrap="none", bg=th["bg"], fg=th["fg"],
                       selectbackground=th["sel_bg"], selectforeground=th["sel_fg"],
                       bd=0, highlightthickness=0, padx=8, pady=6)
        sy = tk.Scrollbar(win, command=text.yview)
        sx = tk.Scrollbar(win, orient="horizontal", command=text.xview)
        text.config(yscrollcommand=sy.set, xscrollcommand=sx.set)
        sy.pack(side="right", fill="y")
        sx.pack(side="bottom", fill="x")
        text.pack(fill="both", expand=True)
        text.tag_configure("add", foreground=th["diff_add"])
        text.tag_configure("del", foreground=th["diff_del"])
        text.tag_configure("hunk", foreground=th["diff_hunk"])
        text.tag_configure("head", foreground=th["gutter_fg"])
        for line in lines:
            if line.startswith(("+++", "---")):
                tag = "head"
            elif line.startswith("+"):
                tag = "add"
            elif line.startswith("-"):
                tag = "del"
            elif line.startswith("@@"):
                tag = "hunk"
            else:
                tag = ()
            text.insert("end", line + "\n", tag)
        text.config(state="disabled")
        win.bind("<Escape>", lambda e: win.destroy())

    def find_in_folder(self):
        if self.fif_win is not None:
            self.fif_win.deiconify()
            self.fif_win.lift()
            self.fif_entry.focus_set()
            return
        doc = self.current()
        w = tk.Toplevel(self.root)
        w.title("Find / Replace in Folder")
        w.geometry("860x520")
        w.protocol("WM_DELETE_WINDOW", w.withdraw)
        self.fif_text = tk.StringVar(value=self.find_var.get())
        self.fif_replace = tk.StringVar()
        self.fif_folder = tk.StringVar(value=os.path.dirname(doc.path) if doc and doc.path
                                       else self.explorer_root)
        self.fif_glob = tk.StringVar(value="*")
        self.fif_case = tk.BooleanVar(value=False)
        self.fif_regex = tk.BooleanVar(value=False)
        self._fif_job = None
        self._fif_results = []
        self._fif_preview = None
        top = tk.Frame(w)
        top.pack(fill="x", padx=8, pady=6)
        top.columnconfigure(1, weight=1)
        rows = (("Find:", self.fif_text), ("Replace:", self.fif_replace),
                ("Folder:", self.fif_folder), ("Files:", self.fif_glob))
        entries = []
        for r, (label, var) in enumerate(rows):
            tk.Label(top, text=label).grid(row=r, column=0, sticky="e")
            entry = tk.Entry(top, textvariable=var)
            entry.grid(row=r, column=1, sticky="ew", padx=4, pady=2)
            entries.append(entry)
        self.fif_entry = entries[0]

        def browse():
            folder = filedialog.askdirectory(parent=w, initialdir=self.fif_folder.get())
            if folder:
                self.fif_folder.set(folder)

        tk.Button(top, text="Search", width=14, command=self._fif_start).grid(row=0, column=2,
                                                                              padx=2)
        tk.Button(top, text="Preview Replace", width=14, command=self._fif_preview_replace).grid(
            row=1, column=2, padx=2)
        tk.Button(top, text="Browse...", width=14, command=browse).grid(row=2, column=2, padx=2)
        tk.Button(top, text="Stop", width=14, command=self._fif_stop).grid(row=3, column=2, padx=2)
        opts = tk.Frame(top)
        opts.grid(row=4, column=1, sticky="w")
        tk.Checkbutton(opts, text="Match case", variable=self.fif_case).pack(side="left")
        tk.Checkbutton(opts, text="Regex", variable=self.fif_regex).pack(side="left")
        self.fif_apply = tk.Button(top, text="Apply Replace", width=14, state="disabled",
                                   command=self._fif_apply_replace)
        self.fif_apply.grid(row=4, column=2, padx=2)
        body = tk.Frame(w)
        body.pack(fill="both", expand=True, padx=8)
        self.fif_list = tk.Listbox(body, font=self.font, activestyle="none")
        sy = tk.Scrollbar(body, command=self.fif_list.yview)
        sx = tk.Scrollbar(body, orient="horizontal", command=self.fif_list.xview)
        self.fif_list.config(yscrollcommand=sy.set, xscrollcommand=sx.set)
        sy.pack(side="right", fill="y")
        sx.pack(side="bottom", fill="x")
        self.fif_list.pack(fill="both", expand=True)
        self.fif_status = tk.Label(w, anchor="w", padx=8)
        self.fif_status.pack(fill="x", pady=4)
        self.fif_list.bind("<Double-Button-1>", self._fif_open)
        self.fif_list.bind("<Return>", self._fif_open)
        self.fif_entry.bind("<Return>", lambda e: self._fif_start())
        w.bind("<Escape>", lambda e: w.withdraw())
        self.fif_win = w
        self.fif_entry.focus_set()

    def _fif_stop(self, message=None):
        if self._fif_job:
            self.root.after_cancel(self._fif_job)
            self._fif_job = None
        if message:
            self.fif_status.config(text=message)

    def _fif_start(self):
        self._fif_stop()
        term = self.fif_text.get()
        folder = self.fif_folder.get()
        if not term:
            return
        if not os.path.isdir(folder):
            self.fif_status.config(text="Folder not found: {folder}".format(folder=folder))
            return
        try:
            pattern = re.compile(term if self.fif_regex.get() else re.escape(term),
                                 0 if self.fif_case.get() else re.IGNORECASE)
        except re.error as e:
            self.fif_status.config(text="Invalid regular expression: {error}".format(
                error=e))
            return
        globs = [g for g in re.split(r"[;,\s]+", self.fif_glob.get()) if g] or ["*"]
        self.fif_list.delete(0, "end")
        self._fif_results = []
        self._fif_files = 0
        self._fif_folder = folder
        self._fif_iter = self._fif_walk(folder, globs, pattern)
        self._fif_job = self.root.after(1, self._fif_step)

    @staticmethod
    def _fif_walk(folder, globs, pattern):
        for dirpath, dirnames, filenames in os.walk(folder):
            dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS)
            for name in sorted(filenames):
                if not any(fnmatch.fnmatch(name.lower(), g.lower()) for g in globs):
                    continue
                yield None
                path = os.path.join(dirpath, name)
                try:
                    if os.path.getsize(path) > FIF_MAX_FILE:
                        continue
                    with open(path, "rb") as f:
                        data = f.read()
                except OSError:
                    continue
                if looks_binary(data):
                    continue
                text = decode_bytes(data)[0]
                for number, line in enumerate(text.splitlines(), 1):
                    m = pattern.search(line)
                    if m:
                        yield path, number, line, m.start()

    def _fif_step(self):
        self._fif_job = None
        deadline = time.monotonic() + 0.05
        done = False
        while time.monotonic() < deadline:
            try:
                item = next(self._fif_iter)
            except StopIteration:
                done = True
                break
            if item is None:
                self._fif_files += 1
                continue
            path, number, line, col = item
            rel = os.path.relpath(path, self._fif_folder)
            self._fif_results.append((path, number, col))
            self.fif_list.insert("end", f"{rel}:{number}:  {line.strip()[:200]}")
            if len(self._fif_results) >= FIF_MAX_RESULTS:
                done = True
                break
        summary = "{matches} matches in {files} files".format(
            matches=f"{len(self._fif_results):,}", files=f"{self._fif_files:,}")
        if done:
            self.fif_status.config(text=summary)
        else:
            self.fif_status.config(text="Searching..." + "  " + summary)
            self._fif_job = self.root.after(1, self._fif_step)

    def _fif_open(self, event=None):
        sel = self.fif_list.curselection()
        if not sel:
            return
        path, number, col = self._fif_results[sel[0]]
        doc = self.open_file(path)
        if doc:
            self._goto(doc, number, col)

    def zoom(self, delta):
        doc = self.current()
        if doc and doc.kind == "image":
            steps = [0.125, 0.25, 0.5, 1, 2, 3, 4, 6, 8]
            cur = min(range(len(steps)), key=lambda i: abs(steps[i] - doc.image_scale))
            doc.image_scale = steps[max(0, min(len(steps) - 1, cur + delta))]
            self.render_image(doc)
            return
        self.set_font_size(self.font_size + delta)

    def reset_zoom(self):
        self.set_font_size(self.cfg.get("base_size", DEFAULT_SIZE))

    def on_ctrl_wheel(self, event):
        up = event.num == 4 or (event.num != 5 and event.delta > 0)
        self.zoom(1 if up else -1)
        return "break"

    def set_font_size(self, size):
        self.font_size = self._clamp(size)
        self.font.configure(size=self.font_size)
        self.apply_text_options()

    def apply_text_options(self):
        for doc in self.docs.values():
            doc.apply_options()
        self.update_status()
        self.save_config()

    def toggle_line_numbers(self):
        for doc in self.docs.values():
            if self.gutter_visible():
                doc.gutter.grid()
                doc.schedule_gutter()
            else:
                doc.gutter.grid_remove()
        self.save_config()

    def refresh_decorations(self):
        for doc in self.docs.values():
            doc.highlight()
            doc.decorate()
            doc.highlight_current_line()
            doc.highlight_occurrences()
            doc.focus_dim()
            doc.update_ruler()
        self.save_config()

    def set_theme(self):
        self.theme = self.themes[self.resolve_theme_name()]
        self._apply_chrome_theme()
        for doc in self.docs.values():
            doc.apply_theme()
            doc.schedule_refresh(10)
            self.update_tab(doc)
        if self.theme_var.get() == "Auto" and self._theme_auto_job is None:
            self._theme_auto_job = self.root.after(60_000, self._auto_theme_tick)
        self.save_config()

    def toggle_split(self):
        doc = self.current()
        if doc:
            split = doc.toggle_split()
            self.set_message("Split view on" if split else "Split view off")

    def toggle_fullscreen(self):
        self.fullscreen = not self.fullscreen
        try:
            self.root.attributes("-fullscreen", self.fullscreen)
        except tk.TclError:
            self.fullscreen = False

    def apply_topmost(self):
        try:
            self.root.attributes("-topmost", self.topmost.get())
        except tk.TclError:
            pass

    def toggle_zen(self):
        self.zen = not self.zen
        if self.zen:
            self._zen_state = {"fullscreen": self.fullscreen, "output": self.output_visible}
            self.root.config(menu="")
            self.status_bar.pack_forget()
            self.activity_bar.pack_forget()
            self.hide_find_bar()
            self.nb.configure(style="Zen.TNotebook")
            self.hide_output()
            if not self.fullscreen:
                self.toggle_fullscreen()
            self.set_message("")
        else:
            self.root.config(menu=self.menubar)
            self.status_bar.pack(side="bottom", fill="x", before=self.hpane)
            self.activity_bar.pack(side="left", fill="y", before=self.hpane)
            self.nb.configure(style=self.tab_style)
            if self.fullscreen != self._zen_state.get("fullscreen", False):
                self.toggle_fullscreen()
            if self._zen_state.get("output"):
                self.show_output()
        self.update_side_panel(save=False)
        self.toggle_line_numbers()
        doc, w = self.cv()
        if w:
            w.focus_set()

    def choose_font(self):
        win = tk.Toplevel(self.root)
        win.title("Font")
        win.transient(self.root)
        win.resizable(False, False)

        families = sorted({f for f in tkfont.families() if not f.startswith("@")}, key=str.lower)
        current = self.font.cget("family")
        frame = tk.Frame(win)
        frame.grid(row=0, column=0, columnspan=2, padx=8, pady=8)
        lb = tk.Listbox(frame, height=14, width=34, exportselection=False)
        sb = tk.Scrollbar(frame, command=lb.yview)
        lb.config(yscrollcommand=sb.set)
        lb.pack(side="left")
        sb.pack(side="left", fill="y")
        for f in families:
            lb.insert("end", f)
        if current in families:
            i = families.index(current)
            lb.selection_set(i)
            lb.see(i)

        tk.Label(win, text="Size:").grid(row=1, column=0, sticky="e", padx=4)
        size_var = tk.StringVar(value=str(self.font_size))
        tk.Spinbox(win, from_=MIN_SIZE, to=MAX_SIZE, textvariable=size_var,
                   width=5).grid(row=1, column=1, sticky="w")
        preview_font = tkfont.Font(win, family=current, size=self.font_size)
        tk.Label(win, text="The quick brown fox 0123 {}[]()", font=preview_font,
                 width=26).grid(row=2, column=0, columnspan=2, pady=8)

        def selection():
            sel = lb.curselection()
            fam = lb.get(sel[0]) if sel else current
            return fam, self._clamp(size_var.get() or self.font_size)

        def update(*_):
            fam, size = selection()
            preview_font.configure(family=fam, size=size)

        def ok():
            fam, size = selection()
            self.font.configure(family=fam)
            self.cfg["base_size"] = size
            self.set_font_size(size)
            win.destroy()

        lb.bind("<<ListboxSelect>>", update)
        size_var.trace_add("write", update)
        buttons = tk.Frame(win)
        buttons.grid(row=3, column=0, columnspan=2, pady=(0, 8))
        tk.Button(buttons, text="OK", width=10, command=ok).pack(side="left", padx=4)
        tk.Button(buttons, text="Cancel", width=10, command=win.destroy).pack(side="left",
                                                                                 padx=4)
        win.bind("<Escape>", lambda e: win.destroy())
        win.grab_set()

    def command_palette(self):
        if self.palette_win is not None:
            try:
                self.palette_win.destroy()
            except tk.TclError:
                pass
        win = tk.Toplevel(self.root)
        self.palette_win = win
        win.title("Command Palette")
        win.transient(self.root)
        x = self.root.winfo_rootx() + max(0, (self.root.winfo_width() - 560) // 2)
        y = self.root.winfo_rooty() + 40
        win.geometry(f"560x380+{x}+{y}")
        query = tk.StringVar()
        entry = tk.Entry(win, textvariable=query, font=self.font)
        entry.pack(fill="x", padx=6, pady=6)
        lb = tk.Listbox(win, font=self.font, activestyle="none", exportselection=False)
        lb.pack(fill="both", expand=True, padx=6, pady=(0, 6))
        shown = []

        def refresh(*_):
            words = query.get().lower().split()
            shown[:] = [item for item in self.palette_items
                        if all(word in item[0].lower() for word in words)]
            lb.delete(0, "end")
            for label, func, accel in shown:
                lb.insert("end", f"{label}    {accel}" if accel else label)
            if shown:
                lb.selection_set(0)
                lb.activate(0)

        def run(event=None):
            sel = lb.curselection()
            if not sel and shown:
                sel = (0,)
            if sel:
                func = shown[sel[0]][1]
                close()
                self.root.after(10, func)
            return "break"

        def move(delta):
            if not shown:
                return "break"
            sel = lb.curselection()
            i = max(0, min(len(shown) - 1, (sel[0] if sel else 0) + delta))
            lb.selection_clear(0, "end")
            lb.selection_set(i)
            lb.activate(i)
            lb.see(i)
            return "break"

        def close(event=None):
            win.destroy()
            self.palette_win = None

        query.trace_add("write", refresh)
        entry.bind("<Return>", run)
        entry.bind("<Down>", lambda e: move(1))
        entry.bind("<Up>", lambda e: move(-1))
        entry.bind("<Escape>", close)
        lb.bind("<Double-Button-1>", run)
        lb.bind("<Return>", run)
        win.bind("<Escape>", close)
        win.protocol("WM_DELETE_WINDOW", close)
        refresh()
        entry.focus_set()

    @staticmethod
    def _runner(path):
        ext = os.path.splitext(path)[1].lower()
        if ext in (".py", ".pyw"):
            python = sys.executable
            if os.path.basename(python).lower() == "pythonw.exe":
                console = os.path.join(os.path.dirname(python), "python.exe")
                if os.path.exists(console):
                    python = console
            return [python, "-u", path]
        if ext in (".bat", ".cmd") and sys.platform != "win32":
            return None
        for candidate in RUNNERS.get(ext, []):
            if shutil.which(candidate[0]):
                return candidate + [path]
        try:
            with open(path, encoding="utf-8", errors="replace") as f:
                first = f.readline().strip()
        except OSError:
            return None
        if first.startswith("#!"):
            try:
                parts = shlex.split(first[2:])
            except ValueError:
                return None
            if parts and (shutil.which(parts[0]) or os.path.isfile(parts[0])):
                return parts + [path]
        return None

    def run_file(self):
        doc = self.current()
        if not doc or doc.kind != "text":
            return
        if doc.lang == "http":
            self.send_http_request()
            return
        if doc.lang == "sql":
            self.run_sql()
            return
        if (not doc.path or doc.modified()) and not self.save(doc):
            return
        cmd = self._runner(doc.path)
        if not cmd:
            messagebox.showinfo(APP, "No program was found to run this type of file.")
            return
        self._start_process(cmd, os.path.dirname(doc.path), doc.name())

    @staticmethod
    def _read_output(proc, out_queue):
        try:
            while True:
                chunk = proc.stdout.read1(4096)
                if not chunk:
                    break
                out_queue.put(chunk)
        except (OSError, ValueError):
            pass
        proc.wait()
        out_queue.put(None)

    def _poll_output(self):
        if self._out_queue is None:
            return
        finished = False
        try:
            while True:
                chunk = self._out_queue.get_nowait()
                if chunk is None:
                    finished = True
                    break
                self._out_append(self._out_decoder.decode(chunk))
        except queue.Empty:
            pass
        if finished:
            code = self.proc.returncode if self.proc else None
            secs = time.monotonic() - self._run_started
            self._out_append("\n" + "[Finished with exit code {code} in {secs} s]".format(
                code=code, secs=f"{secs:.1f}") + "\n", "info" if code == 0 else "error")
            self.set_message("Program finished")
            self._out_queue = None
            self.proc = None
        else:
            self.root.after(50, self._poll_output)

    def stop_run(self):
        if self.proc and self.proc.poll() is None:
            try:
                self.proc.kill()
            except OSError:
                pass
            self._out_append("\n" + "[Stopped]" + "\n", "error")

    def show_output(self):
        if not self.output_visible:
            self.main_pane.add(self.bottom_nb, stretch="never", height=220)
            self.output_visible = True
        self.bottom_nb.select(self.out_frame)

    def hide_output(self):
        if self.output_visible:
            self.main_pane.forget(self.bottom_nb)
            self.output_visible = False

    def toggle_output(self):
        if self.output_visible:
            self.hide_output()
        else:
            self.show_output()

    def clear_output(self):
        self.out_text.config(state="normal")
        self.out_text.delete("1.0", "end")
        self.out_text.config(state="disabled")

    def _out_append(self, text, tag=None):
        self.out_text.config(state="normal")
        self.out_text.insert("end", text, tag or ())
        self.out_text.config(state="disabled")
        self.out_text.see("end")

    def _output_jump(self, event):
        index = self.out_text.index(f"@{event.x},{event.y}")
        line = self.out_text.get(f"{index} linestart", f"{index} lineend")
        for pattern in (r'File "([^"]+)", line (\d+)', r"\(([^()]+?):(\d+):\d+\)",
                        r"^\s*(.+?):(\d+)(?::\d+)?:"):
            m = re.search(pattern, line)
            if not m:
                continue
            path = m.group(1)
            if not os.path.isabs(path) and self._run_cwd:
                path = os.path.join(self._run_cwd, path)
            if os.path.isfile(path):
                doc = self.open_file(path)
                if doc:
                    self._goto(doc, int(m.group(2)))
                return "break"
        return None

    def preview(self):
        doc = self.current()
        if not doc:
            return
        ext = os.path.splitext(doc.path or doc.display_name or "")[1].lower()
        if doc.lang == "markdown":
            page = markdown_to_html(doc.content(), doc.name())
            if doc.path:
                url = self._serve_preview(doc.path, page, ".preview.html")
                if url:
                    webbrowser.open(url)
                    self.set_message("Preview opened in your browser")
                    return
            target = os.path.join(tempfile.gettempdir(), f"notepad_preview_{doc.id}.html")
            with open(target, "w", encoding="utf-8") as f:
                f.write(page)
            webbrowser.open(Path(target).as_uri())
            self.set_message("Preview opened in your browser")
            return
        if ext in (".html", ".htm", ".xhtml", ".svg") or doc.lang == "markup":
            if doc.path:
                url = self._serve_preview(doc.path, doc.content(), "")
                if url:
                    webbrowser.open(url)
                    self.set_message(f"Preview served at {url} (unsaved changes included)")
                    return
            target = os.path.join(tempfile.gettempdir(), f"notepad_preview_{doc.id}.html")
            with open(target, "w", encoding="utf-8") as f:
                f.write(doc.content())
            webbrowser.open(Path(target).as_uri())
            return
        messagebox.showinfo(APP, "Preview is available for HTML and Markdown files.")

    def _build_find_dialog(self):
        w = tk.Toplevel(self.root)
        w.title("Find & Replace")
        w.transient(self.root)
        w.resizable(False, False)
        w.protocol("WM_DELETE_WINDOW", w.withdraw)

        tk.Label(w, text="Find:").grid(row=0, column=0, sticky="e", padx=6, pady=4)
        self.find_entry = tk.Entry(w, width=34, textvariable=self.find_var)
        self.find_entry.grid(row=0, column=1, padx=4, pady=4)
        tk.Label(w, text="Replace:").grid(row=1, column=0, sticky="e", padx=6, pady=4)
        self.replace_entry = tk.Entry(w, width=34, textvariable=self.replace_var)
        self.replace_entry.grid(row=1, column=1, padx=4, pady=4)

        opts = tk.Frame(w)
        opts.grid(row=2, column=1, sticky="w")
        for text, var in (("Match case", self.opt_case), ("Whole word", self.opt_word),
                          ("Regex", self.opt_regex)):
            tk.Checkbutton(opts, text=text, variable=var,
                           command=self.save_config).pack(side="left")

        btns = tk.Frame(w)
        btns.grid(row=0, column=2, rowspan=4, sticky="n", padx=6, pady=4)
        for text, cmd in (("Find Next", self.find_next), ("Find Previous", self.find_prev),
                          ("Replace", self.replace_one), ("Replace All", self.replace_all),
                          ("Close", w.withdraw)):
            tk.Button(btns, text=text, width=14, command=cmd).pack(fill="x", pady=1)

        for entry in (self.find_entry, self.replace_entry):
            entry.bind("<Return>", lambda e: self.find_next())
            entry.bind("<Shift-Return>", lambda e: self.find_prev())
        w.bind("<Escape>", lambda e: w.withdraw())
        w.bind("<F3>", lambda e: self.find_next())
        w.bind("<Shift-F3>", lambda e: self.find_prev())
        self.find_win = w

    def show_find(self, replace=False):
        if self.find_win is None:
            self._build_find_dialog()
        doc, w = self.cv()
        if doc and w.tag_ranges("sel"):
            selected = w.get("sel.first", "sel.last")
            if selected and "\n" not in selected and len(selected) < 200:
                self.find_var.set(selected)
        self.find_win.deiconify()
        self.find_win.lift()
        entry = self.replace_entry if replace and self.find_var.get() else self.find_entry
        entry.focus_set()
        entry.select_range(0, "end")

    def _pattern(self):
        term = self.find_var.get()
        if not term:
            return None
        pat = term if self.opt_regex.get() else re.escape(term)
        if self.opt_word.get():
            pat = rf"\b(?:{pat})\b"
        flags = re.MULTILINE | (0 if self.opt_case.get() else re.IGNORECASE)
        try:
            return re.compile(pat, flags)
        except re.error as e:
            self.set_message("Invalid regular expression: {error}".format(error=e))
            self.root.bell()
            return None

    @staticmethod
    def _offset(text, index):
        return len(text.get("1.0", index))

    def _search(self, backward=False):
        doc, t = self.cv()
        if not doc:
            return False
        if not self.find_var.get():
            self.show_find_bar()
            return False
        pattern = self._pattern()
        if not pattern:
            return False
        content = doc.content()
        sel = t.tag_ranges("sel")
        if sel:
            start, end = self._offset(t, sel[0]), self._offset(t, sel[1])
        else:
            start = end = self._offset(t, "insert")
        wrapped = False
        if backward:
            found = [m for m in pattern.finditer(content, 0, start) if m.end() > m.start()]
            if not found:
                wrapped = True
                found = [m for m in pattern.finditer(content) if m.end() > m.start()]
            m = found[-1] if found else None
        else:
            m = next((x for x in pattern.finditer(content, end) if x.end() > x.start()), None)
            if not m:
                wrapped = True
                m = next((x for x in pattern.finditer(content) if x.end() > x.start()), None)
        if not m:
            self.set_message(f"Not found: {self.find_var.get()}")
            self.root.bell()
            return False
        s, e = f"1.0+{m.start()}c", f"1.0+{m.end()}c"
        old_line = int(t.index("insert").split(".")[0])
        new_line = int(t.index(s).split(".")[0])
        if abs(new_line - old_line) > 1:
            self.push_nav(doc, t.index("insert"))
        doc.reveal(t.index(s))
        t.tag_remove("sel", "1.0", "end")
        t.tag_add("sel", s, e)
        t.mark_set("insert", s if backward else e)
        t.see(s)
        message = f"Found at line {new_line}"
        if wrapped:
            message = "Search wrapped around - " + message
        self.set_message(message)
        if self.find_bar_visible:
            self._find_bar_changed()
        return True

    def find_next(self):
        return self._search(False)

    def find_prev(self):
        return self._search(True)

    def _replacement(self, match):
        repl = self.replace_var.get()
        return match.expand(repl) if self.opt_regex.get() else repl

    def replace_one(self):
        doc, t = self.cv()
        pattern = self._pattern()
        if not pattern or not self._editable(doc):
            return
        sel = t.tag_ranges("sel")
        if sel:
            first, last = t.index(sel[0]), t.index(sel[1])
            m = pattern.fullmatch(t.get(first, last))
            if m:
                try:
                    repl = self._replacement(m)
                except (re.error, IndexError) as e:
                    self.set_message("Bad replacement: {error}".format(error=e))
                    return
                self.edit_block(doc, t, first, last, repl, keep_cursor=False)
                t.mark_set("insert", f"{first}+{len(repl)}c")
        self._search(False)

    def replace_all(self):
        doc, t = self.cv()
        pattern = self._pattern()
        if not pattern or not self._editable(doc):
            return
        try:
            new, count = pattern.subn(self._replacement, doc.content())
        except (re.error, IndexError) as e:
            self.set_message("Bad replacement: {error}".format(error=e))
            return
        if not count:
            self.set_message("Not found: {term}".format(term=self.find_var.get()))
            self.root.bell()
            return
        self.edit_block(doc, t, "1.0", "end-1c", new)
        self.set_message("Replaced {count} occurrence(s)".format(count=f"{count:,}"))

    def start(self, paths, stdin_text=None):
        self._restore_session()
        self._recover()
        self.handle_args(paths, stdin_text)
        if not self.docs:
            self.new_tab()
        self.update_side_panel(save=False)
        if self.single_instance.get():
            self.instance_serve()
        self.root.after(RECOVERY_INTERVAL, self._recovery_tick)
        self.root.after(DISK_CHECK_INTERVAL, self._disk_tick)
        self.root.after(AUTO_SAVE_INTERVAL, self._auto_save_tick)
        if self.theme_var.get() == "Auto":
            self._theme_auto_job = self.root.after(60_000, self._auto_theme_tick)

    def exit(self):
        for doc in self.ordered_docs():
            if doc.modified() and not doc.scratch:
                self.nb.select(doc.frame)
                if not self._confirm_discard(doc):
                    return False
        if self.proc and self.proc.poll() is None:
            self.proc.kill()
        for doc in self.docs.values():
            if doc.scratch:
                self.save_scratch(doc)
            self.save_undo_history(doc)
        self._save_session()
        for doc in self.docs.values():
            self._remove_recovery(doc)
        maximized = False
        try:
            maximized = self.root.state() == "zoomed"
        except tk.TclError:
            pass
        self.cfg["maximized"] = maximized
        if not maximized and not self.fullscreen:
            self.cfg["geometry"] = self.root.geometry()
        self.save_config()
        self.instance_stop()
        if self.preview_server:
            threading.Thread(target=self.preview_server.shutdown, daemon=True).start()
        for doc in self.docs.values():
            doc.cancel_jobs()
        try:
            pending = self.root.tk.splitlist(self.root.tk.call("after", "info"))
        except tk.TclError:
            pending = ()
        for job in pending:
            try:
                self.root.tk.call("after", "cancel", job)
            except tk.TclError:
                pass
        self.root.destroy()
        return True

    def _build_commands(self):
        self.commands = {}
        self.command_order = []

        def add(cid, label, func, keys=(), kind="cmd", var=None, value=None, accel=None,
                menu=""):
            self.commands[cid] = {"label": label, "func": func, "keys": list(keys), "kind": kind,
                                  "var": var, "value": value, "accel": accel, "menu": menu}
            self.command_order.append(cid)

        def check(cid, label, var, func, keys=(), menu=""):
            add(cid, label, func, keys, kind="check", var=var, menu=menu)

        def radio(cid, label, var, value, func, menu=""):
            add(cid, label, func, (), kind="radio", var=var, value=value, menu=menu)

        M = "File"
        add("file.new", "New Tab", self.new_tab, ["<Control-n>"], menu=M)
        add("file.new_template", "New from Template...", self.new_from_template, menu=M)
        add("file.open", "Open...", self.open_file, ["<Control-o>"], menu=M)
        add("file.open_folder", "Open Folder in Explorer...", self.open_folder_explorer, menu=M)
        add("file.open_ftp", "Open from FTP...", self.open_ftp, menu=M)
        add("file.open_archive", "Open Archive...", self.open_archive, menu=M)
        add("file.scratchpad", "Scratchpad", self.open_scratchpad, menu=M)
        add("file.reload", "Reload from Disk", self.reload, menu=M)
        add("file.save", "Save", self.save, ["<Control-s>"], menu=M)
        add("file.save_as", "Save As...", self.save_as, ["<Control-Shift-S>"], menu=M)
        add("file.save_all", "Save All", self.save_all, ["<Control-Alt-s>"], menu=M)
        add("file.rename", "Rename File...", self.rename_file, menu=M)
        add("file.duplicate", "Duplicate File...", self.duplicate_file, menu=M)
        add("file.compare_saved", "Compare with Saved", self.compare_saved, menu=M)
        add("file.compare", "Compare With...", self.compare_with, menu=M)
        add("file.compare_folders", "Compare Folders...", self.compare_folders, menu=M)
        add("file.history", "Local History...", self.local_history, menu=M)
        add("file.find_in_folder", "Find / Replace in Folder...", self.find_in_folder,
            ["<Control-Shift-F>"], menu=M)
        add("file.todo", "TODO List...", self.todo_list, menu=M)
        add("file.convert_utf8", "Convert Folder to UTF-8...", self.convert_folder_utf8, menu=M)
        add("file.export_html", "Export as HTML...", self.export_html_file, menu=M)
        add("file.export_pdf", "Export as PDF...", self.export_pdf_file, menu=M)
        add("file.print", "Print...", self.print_file, ["<Control-p>"], menu=M)
        add("file.reveal", "Open Containing Folder", self.reveal_file, menu=M)
        add("file.copy_path", "Copy Path", self.copy_path, menu=M)
        add("file.new_window", "Move Tab to New Window", self.move_to_new_window, menu=M)
        add("file.close", "Close Tab", self.close_tab, ["<Control-w>"], menu=M)
        add("file.close_others", "Close Other Tabs", self.close_other_tabs, menu=M)
        add("file.close_right", "Close Tabs to the Right", self.close_tabs_right, menu=M)
        add("file.close_all", "Close All Tabs", self.close_all_tabs, menu=M)
        check("file.restore_session", "Restore Session on Startup", self.restore_session,
              self.save_config, menu=M)
        check("file.single_instance", "Open Files in the Running Window", self.single_instance,
              self.save_config, menu=M)
        add("file.exit", "Exit", self.exit, ["<Control-q>"], menu=M)

        M = "Edit"
        add("edit.undo", "Undo", lambda: self._text_event("<<Undo>>"), accel="Ctrl+Z", menu=M)
        add("edit.redo", "Redo", lambda: self._text_event("<<Redo>>"),
            ["<Control-y>", "<Control-Shift-Z>"], menu=M)
        add("edit.undo_session", "Undo Previous Session Changes", self.undo_previous_session,
            menu=M)
        add("edit.cut", "Cut", lambda: self._text_event("<<Cut>>"), accel="Ctrl+X", menu=M)
        add("edit.copy", "Copy", lambda: self._text_event("<<Copy>>"), accel="Ctrl+C", menu=M)
        add("edit.paste", "Paste", lambda: self._text_event("<<Paste>>"), accel="Ctrl+V", menu=M)
        add("edit.paste_history", "Paste from History...", self.paste_from_history,
            ["<Control-Alt-v>"], menu=M)
        add("edit.select_all", "Select All", self.select_all, ["<Control-a>"], menu=M)
        add("edit.expand", "Expand Selection", self.expand_selection, ["<Shift-Alt-Right>"],
            menu=M)
        add("edit.shrink", "Shrink Selection", self.shrink_selection, ["<Shift-Alt-Left>"],
            menu=M)
        add("edit.comment", "Toggle Comment", self.toggle_comment,
            ["<Control-slash>", "<Control-KP_Divide>"], menu=M)
        add("edit.duplicate", "Duplicate Line", self.duplicate_line, ["<Control-d>"], menu=M)
        add("edit.move_up", "Move Line Up", lambda: self.move_lines(-1), ["<Alt-Up>"], menu=M)
        add("edit.move_down", "Move Line Down", lambda: self.move_lines(1), ["<Alt-Down>"],
            menu=M)
        add("edit.delete_line", "Delete Line", self.delete_line, ["<Control-Shift-K>"], menu=M)
        add("edit.join", "Join Lines", self.join_lines, ["<Control-j>"], menu=M)
        add("edit.indent", "Indent", lambda: self.indent_cmd(False), accel="Tab", menu=M)
        add("edit.unindent", "Unindent", lambda: self.indent_cmd(True), accel="Shift+Tab",
            menu=M)
        add("edit.rename", "Rename in File...", self.rename_symbol, ["<F4>"], menu=M)
        add("edit.increment", "Increment Number", lambda: self.step_number(1),
            ["<Control-Alt-Up>"], menu=M)
        add("edit.decrement", "Decrement Number", lambda: self.step_number(-1),
            ["<Control-Alt-Down>"], menu=M)
        add("edit.autocomplete", "Autocomplete", self.autocomplete, ["<Control-space>"], menu=M)
        add("bm.toggle", "Toggle Bookmark", self.toggle_bookmark, ["<Control-F2>"], menu=M)
        add("bm.next", "Next Bookmark", lambda: self.goto_bookmark(1), ["<F2>"], menu=M)
        add("bm.prev", "Previous Bookmark", lambda: self.goto_bookmark(-1), ["<Shift-F2>"],
            menu=M)
        add("bm.clear", "Clear Bookmarks", self.clear_bookmarks, menu=M)
        add("fold.toggle", "Toggle Fold", self.toggle_fold, ["<F6>"], menu=M)
        add("fold.all", "Fold All", self.fold_all, ["<Control-F6>"], menu=M)
        add("fold.none", "Unfold All", self.unfold_all, ["<Shift-F6>"], menu=M)
        add("insert.datetime", "Insert Date/Time", self.insert_datetime, ["<F5>"], menu=M)
        add("insert.timestamp", "Insert Unix Timestamp", self.insert_timestamp, menu=M)
        add("insert.uuid", "Insert UUID", self.insert_uuid, menu=M)
        add("insert.special", "Insert Special Character...", self.special_characters, menu=M)
        add("insert.password", "Generate Password...", self.password_generator, menu=M)
        add("insert.color", "Pick Color...", self.pick_color, ["<Control-Shift-C>"], menu=M)
        add("insert.file", "Insert File...", self.insert_file, menu=M)
        add("insert.testdata", "Generate Test Data...", self.test_data_dialog, menu=M)
        check("edit.read_only", "Read Only", self.ro_var, self.toggle_read_only, menu=M)
        check("edit.vim", "Vim Mode", self.vim_var, self.toggle_vim, menu=M)
        add("macro.record", "Start / Stop Recording Macro", self.toggle_macro_recording,
            ["<F8>"], menu=M)
        add("macro.play", "Play Macro", self.play_macro, ["<Shift-F8>"], menu=M)

        M = "Search"
        add("search.find", "Find...", self.show_find_bar, ["<Control-f>"], menu=M)
        add("search.replace", "Replace...", lambda: self.show_find(True), ["<Control-h>"],
            menu=M)
        add("search.next", "Find Next", self.find_next, ["<F3>"], menu=M)
        add("search.prev", "Find Previous", self.find_prev, ["<Shift-F3>"], menu=M)
        add("search.goto_line", "Go To Line...", self.goto_line, ["<Control-g>"], menu=M)
        add("search.symbol", "Go To Symbol...", self.goto_symbol, ["<Control-Shift-O>"], menu=M)
        add("search.definition", "Go To Definition", self.goto_definition, ["<F12>"], menu=M)
        add("search.back", "Go Back", self.nav_go_back, ["<Alt-Left>"], menu=M)
        add("search.forward", "Go Forward", self.nav_go_forward, ["<Alt-Right>"], menu=M)
        add("search.filter", "Filter Lines View...", self.filter_view, menu=M)
        add("search.clear_filter", "Clear Line Filter", self.clear_filter, menu=M)

        M = "View"
        check("view.explorer", "Explorer", self.explorer_var, self._on_explorer_check,
              ["<Control-Shift-E>"], menu=M)
        check("view.outline", "Outline", self.outline_var, self._on_outline_check,
              ["<Control-Shift-J>"], menu=M)
        add("view.output", "Output Panel", self.toggle_output, menu=M)
        add("view.console", "Python Console", self.show_console, ["<Control-Shift-Y>"], menu=M)
        add("view.md_preview", "Markdown Preview Pane", self.toggle_md_preview,
            ["<Control-Shift-M>"], menu=M)
        check("view.minimap", "Minimap", self.show_minimap, self.toggle_minimap, menu=M)
        add("view.split", "Split View", self.toggle_split, ["<Control-backslash>"], menu=M)
        add("view.side_by_side", "Side by Side With...", self.side_by_side, menu=M)
        check("view.line_numbers", "Line Numbers", self.line_numbers, self.toggle_line_numbers,
              menu=M)
        check("view.highlight", "Syntax Highlighting", self.highlight, self.refresh_decorations,
              menu=M)
        check("view.curline", "Highlight Current Line", self.hl_line, self.refresh_decorations,
              menu=M)
        check("view.occurrences", "Highlight Occurrences", self.hl_occ, self.refresh_decorations,
              menu=M)
        check("view.rainbow", "Rainbow Brackets", self.rainbow, self.refresh_decorations, menu=M)
        check("view.swatches", "Color Swatches", self.swatches, self.refresh_decorations, menu=M)
        check("view.guides", "Indent Guides", self.show_guides, self.refresh_decorations, menu=M)
        check("view.whitespace", "Show Whitespace", self.show_ws, self.refresh_decorations,
              menu=M)
        check("view.trailing", "Highlight Trailing Spaces", self.show_trailing,
              self.refresh_decorations, menu=M)
        check("view.long", "Mark Long Lines", self.mark_long, self.refresh_decorations, menu=M)
        check("view.ruler", "Show Ruler", self.show_ruler, self.refresh_decorations, menu=M)
        radio("theme.Auto", "Auto (System)", self.theme_var, "Auto", self.set_theme, menu=M)
        for name in self.themes:
            radio(f"theme.{name}", name, self.theme_var, name, self.set_theme, menu=M)
        for pct in ("100", "125", "150", "175", "200"):
            radio(f"scale.{pct}", f"{pct}%", self.ui_scale, pct, self.apply_ui_scale, menu=M)
        add("view.fullscreen", "Full Screen", self.toggle_fullscreen, ["<F11>"], menu=M)
        add("view.zen", "Zen Mode", self.toggle_zen, ["<Shift-F11>"], menu=M)
        check("view.typewriter", "Typewriter Mode", self.typewriter, self.refresh_decorations,
              menu=M)
        check("view.focus", "Focus Mode", self.focus_mode, self.refresh_decorations, menu=M)
        check("view.topmost", "Always on Top", self.topmost, self.apply_topmost, menu=M)
        add("view.zoom_in", "Zoom In", lambda: self.zoom(1),
            ["<Control-plus>", "<Control-equal>", "<Control-KP_Add>"], menu=M)
        add("view.zoom_out", "Zoom Out", lambda: self.zoom(-1),
            ["<Control-minus>", "<Control-KP_Subtract>"], menu=M)
        add("view.zoom_reset", "Reset Zoom", self.reset_zoom, ["<Control-0>"], menu=M)
        add("view.next_tab", "Next Tab", lambda: self.cycle_tab(1), ["<Control-Tab>"], menu=M)
        add("view.prev_tab", "Previous Tab", lambda: self.cycle_tab(-1),
            ["<Control-Shift-Tab>", "<Control-ISO_Left_Tab>"], menu=M)
        add("view.palette", "Command Palette...", self.command_palette, ["<Control-Shift-P>"],
            menu=M)

        M = "Format"
        check("fmt.wrap", "Word Wrap", self.wrap, self.apply_text_options, menu=M)
        check("fmt.auto_indent", "Auto Indent", self.auto_indent, self.save_config, menu=M)
        check("fmt.auto_close", "Auto Close Brackets, Quotes and Tags", self.auto_close,
              self.save_config, menu=M)
        check("fmt.spaces", "Indent with Spaces", self.use_spaces, self.set_indent_style, menu=M)
        for n in (2, 4, 8):
            radio(f"tab.{n}", str(n), self.tab_width, n, self.set_indent_style, menu=M)
        check("fmt.detect", "Detect Indentation on Open", self.detect_indent, self.save_config,
              menu=M)
        add("fmt.to_spaces", "Convert Indentation to Spaces", lambda: self.convert_indent(True),
            menu=M)
        add("fmt.to_tabs", "Convert Indentation to Tabs", lambda: self.convert_indent(False),
            menu=M)
        check("fmt.trim", "Trim Trailing Spaces on Save", self.trim_on_save, self.save_config,
              menu=M)
        check("fmt.bak", "Create .bak Backup on Save", self.backup_bak, self.save_config, menu=M)
        check("fmt.autosave", "Auto Save", self.auto_save, self.save_config, menu=M)
        add("fmt.font", "Font...", self.choose_font, menu=M)
        add("fmt.ruler_col", "Ruler Column...", self.set_ruler_column, menu=M)
        add("fmt.settings", "Settings...", self.settings_window, ["<Control-comma>"], menu=M)
        radio("lang.auto", "Auto Detect", self.lang_var, "auto", self.set_language_mode, menu=M)
        radio("lang.text", "Plain Text", self.lang_var, "text", self.set_language_mode, menu=M)
        for lang, label in LANG_NAMES.items():
            radio(f"lang.{lang}", label, self.lang_var, lang, self.set_language_mode, menu=M)

        M = "Encoding"
        for enc in ENCODINGS:
            radio(f"enc.{enc}", f"Save as {enc}", self.enc_var, enc, self.set_encoding, menu=M)
            add(f"reopen.{enc}", f"Reopen with {enc}", lambda e=enc: self.reload(encoding=e),
                menu=M)
        for name in EOLS:
            radio(f"eol.{name}", name, self.eol_var, name, self.set_eol, menu=M)

        M = "Tools"
        add("case.upper", "UPPERCASE", lambda: self.change_case("upper"), ["<Control-Shift-U>"],
            menu=M)
        add("case.lower", "lowercase", lambda: self.change_case("lower"), ["<Control-Shift-L>"],
            menu=M)
        add("case.title", "Title Case", lambda: self.change_case("title"), menu=M)
        for style, label in (("snake", "snake_case"), ("camel", "camelCase"),
                             ("pascal", "PascalCase"), ("kebab", "kebab-case"),
                             ("constant", "CONSTANT_CASE")):
            add(f"case.{style}", label, lambda s=style: self.convert_case_cmd(s), menu=M)
        add("lines.sort", "Sort Lines", self.sort_lines, menu=M)
        add("lines.unique", "Remove Duplicate Lines", self.unique_lines, menu=M)
        add("lines.reverse", "Reverse Lines", self.reverse_lines, menu=M)
        add("lines.shuffle", "Shuffle Lines", self.shuffle_lines, menu=M)
        add("lines.number", "Number Lines", self.number_lines, menu=M)
        add("lines.keep", "Keep Lines Matching...", lambda: self.filter_lines(True), menu=M)
        add("lines.remove", "Remove Lines Matching...", lambda: self.filter_lines(False), menu=M)
        add("lines.trim", "Trim Trailing Spaces", self.trim_trailing, menu=M)
        add("lines.align", "Align Columns...", self.align_columns, menu=M)
        add("lines.wrap", "Wrap Paragraph", self.wrap_paragraph, menu=M)
        add("clean.invisible", "Remove Invisible Characters", self.clean_invisible_cmd, menu=M)
        add("clean.quotes", "Straighten Quotes", self.straighten_quotes_cmd, menu=M)
        add("clean.nfc", "Normalize Unicode (NFC)", self.normalize_unicode, menu=M)
        add("esc.html", "Escape HTML", lambda: self.escape_tool("html_e"), menu=M)
        add("esc.unhtml", "Unescape HTML", lambda: self.escape_tool("html_d"), menu=M)
        add("esc.json", "Escape JSON String", lambda: self.escape_tool("json_e"), menu=M)
        add("esc.unjson", "Unescape JSON String", lambda: self.escape_tool("json_d"), menu=M)
        add("esc.regex", "Escape Regex", lambda: self.escape_tool("regex"), menu=M)
        add("data.json_fmt", "Format JSON", lambda: self.format_json(False), menu=M)
        add("data.json_min", "Minify JSON", lambda: self.format_json(True), menu=M)
        add("data.json_sort", "Sort JSON Keys", self.sort_json_keys, menu=M)
        add("data.xml", "Format XML", self.format_xml, menu=M)
        add("data.validate", "Validate Syntax", self.validate_cmd, ["<F7>"], menu=M)
        add("data.json_tree", "JSON Tree View", self.json_tree, menu=M)
        add("data.csv", "CSV Table View", self.csv_table, menu=M)
        add("code.b64e", "Base64 Encode", lambda: self.codec_tool("b64e"), menu=M)
        add("code.b64d", "Base64 Decode", lambda: self.codec_tool("b64d"), menu=M)
        add("code.urle", "URL Encode", lambda: self.codec_tool("urle"), menu=M)
        add("code.urld", "URL Decode", lambda: self.codec_tool("urld"), menu=M)
        for algo in ("MD5", "SHA-1", "SHA-256"):
            add(f"hash.{algo}", f"Hash {algo}", lambda a=algo: self.show_hash(a), menu=M)
        for base, label in (("dec", "Decimal"), ("hex", "Hexadecimal"), ("bin", "Binary"),
                            ("oct", "Octal")):
            add(f"num.{base}", f"Number to {label}", lambda b=base: self.convert_number(b),
                menu=M)
        add("time.convert", "Timestamp <-> Date", self.convert_timestamp, menu=M)
        add("tools.calc", "Calculate Selection", self.calculate, menu=M)
        add("tools.stats", "Text Statistics", self.text_statistics, menu=M)
        add("tools.goal", "Set Word Goal...", self.set_word_goal, menu=M)
        add("tools.pomodoro", "Start / Stop Pomodoro", self.toggle_pomodoro, menu=M)
        add("tools.regex", "Regex Tester...", self.regex_tester, menu=M)
        add("tools.sql", "Run SQL on SQLite...", self.run_sql, menu=M)
        add("tools.http", "Send HTTP Request", self.send_http_request, menu=M)
        add("md.bold", "Markdown Bold", lambda: self.md_wrap("**"), ["<Control-b>"], menu=M)
        add("md.italic", "Markdown Italic", lambda: self.md_wrap("*"), ["<Control-i>"], menu=M)
        add("md.toc", "Insert Table of Contents", self.insert_toc, menu=M)
        add("tools.hex", "View as Hex", self.view_as_hex, menu=M)
        add("tools.follow", "Follow File (Tail)", self.toggle_follow, menu=M)
        add("custom.snippets", "Edit Snippets", self.edit_snippets, menu=M)
        add("custom.templates", "Open Templates Folder", self.open_templates_folder, menu=M)
        add("custom.keys", "Edit Keybindings", self.edit_keybindings, menu=M)
        add("custom.themes", "Edit Themes", self.edit_themes, menu=M)

        M = "Run"
        add("run.file", "Run File", self.run_file, ["<Control-r>"], menu=M)
        add("run.selection", "Run Selection", self.run_selection, ["<Control-Shift-Return>"],
            menu=M)
        add("run.tests", "Run Tests", self.run_tests, ["<Control-Shift-T>"], menu=M)
        add("run.profile", "Run with Profiler", self.run_profiler, menu=M)
        add("run.stop", "Stop", self.stop_run, menu=M)
        add("run.preview", "Preview in Browser", self.preview, ["<Control-Shift-V>"], menu=M)
        add("run.clear", "Clear Output", self.clear_output, menu=M)

        M = "Help"
        add("help.keys", "Keyboard Shortcuts", self.shortcuts_window, ["<F1>"], menu=M)
        add("help.doc", "Show Documentation", self.show_documentation, ["<Shift-F1>"], menu=M)
        add("help.folder", "Open Settings Folder", self.open_settings_folder, menu=M)
        add("help.errors", "Open Error Log", self.open_error_log, menu=M)
        add("help.reset", "Reset Settings...", self.reset_settings, menu=M)
        add("help.portable", "Portable Mode...", self.toggle_portable, menu=M)
        add("help.shortcut", "Create Desktop Shortcut", self.create_desktop_shortcut, menu=M)
        add("help.selftest", "Run Self-Test", self.run_self_test_process, menu=M)
        add("help.about", "About", self.about, menu=M)

        overrides = load_json_file(KEYBINDINGS_FILE, {})
        if isinstance(overrides, dict):
            for cid, keys in overrides.items():
                if cid in self.commands:
                    if isinstance(keys, str):
                        keys = [keys] if keys else []
                    if isinstance(keys, list):
                        self.commands[cid]["keys"] = [k for k in keys if isinstance(k, str)]
        self._build_shortcuts()

    def run_command(self, cid):
        cmd = self.commands.get(cid)
        if cmd:
            if cmd["kind"] == "check":
                cmd["var"].set(not cmd["var"].get())
            elif cmd["kind"] == "radio":
                cmd["var"].set(cmd["value"])
            cmd["func"]()
        return "break"

    def accel(self, cid):
        cmd = self.commands[cid]
        if cmd["accel"]:
            return cmd["accel"]
        return seq_to_accel(cmd["keys"][0]) if cmd["keys"] else ""

    def rebind_shortcuts(self):
        old = {seq for seq, _ in self.shortcuts}
        self._build_commands()
        widgets = [self.root] + [w for d in self.docs.values() for w in d.views()]
        for w in widgets:
            for seq in old:
                try:
                    w.unbind(seq)
                except tk.TclError:
                    pass
            self.bind_shortcuts(w)
        self._build_menu()

    def _menu_layout(self):
        return [
            ("File", ["file.new", "file.new_template", "file.open", ("recent",), "file.open_folder",
                      "file.open_ftp", "file.open_archive", "file.scratchpad", "file.reload", "-",
                      "file.save", "file.save_as", "file.save_all", "file.rename",
                      "file.duplicate", "-",
                      ("Compare", ["file.compare_saved", "file.compare", "file.compare_folders",
                                   "file.history"]),
                      ("Folder Tools", ["file.find_in_folder", "file.todo", "file.convert_utf8"]),
                      ("Export", ["file.export_html", "file.export_pdf"]), "file.print", "-",
                      "file.reveal", "file.copy_path", "file.new_window", "-", "file.close",
                      "file.close_others", "file.close_right", "file.close_all", "-",
                      "file.restore_session", "file.single_instance", "file.exit"]),
            ("Edit", ["edit.undo", "edit.redo", "edit.undo_session", "-", "edit.cut", "edit.copy",
                      "edit.paste", "edit.paste_history", "edit.select_all", "-",
                      ("Selection", ["edit.expand", "edit.shrink"]),
                      ("Line", ["edit.comment", "edit.duplicate", "edit.move_up",
                                "edit.move_down", "edit.delete_line", "edit.join",
                                "edit.indent", "edit.unindent"]),
                      "edit.rename", "edit.increment", "edit.decrement", "edit.autocomplete", "-",
                      ("Bookmarks", ["bm.toggle", "bm.next", "bm.prev", "bm.clear"]),
                      ("Folding", ["fold.toggle", "fold.all", "fold.none"]),
                      ("Insert", ["insert.datetime", "insert.timestamp", "insert.uuid",
                                  "insert.special", "insert.password", "insert.color",
                                  "insert.file", "insert.testdata"]),
                      ("Macro", ["macro.record", "macro.play"]), "-",
                      "edit.read_only", "edit.vim"]),
            ("Search", ["search.find", "search.replace", "search.next", "search.prev", "-",
                        "search.goto_line", "search.symbol", "search.definition", "search.back",
                        "search.forward", "-", "search.filter", "search.clear_filter", "-",
                        "file.find_in_folder"]),
            ("View", ["view.explorer", "view.outline", "view.output", "view.console",
                      "view.md_preview", "view.minimap", "-", "view.split", "view.side_by_side",
                      "-",
                      ("Editor Display", ["view.line_numbers", "view.highlight", "view.curline",
                                          "view.occurrences", "view.rainbow", "view.swatches",
                                          "view.guides", "view.whitespace", "view.trailing",
                                          "view.long", "view.ruler"]),
                      ("Theme", ["theme.Auto"] + [f"theme.{n}" for n in self.themes]),
                      ("Interface Scale", [f"scale.{p}" for p in ("100", "125", "150", "175",
                                                                  "200")]),
                      "-", "view.fullscreen", "view.zen", "view.typewriter", "view.focus",
                      "view.topmost", "-", "view.zoom_in", "view.zoom_out", "view.zoom_reset",
                      "-", "view.next_tab", "view.prev_tab", "-", "view.palette"]),
            ("Format", ["fmt.wrap", "fmt.auto_indent", "fmt.auto_close", "-", "fmt.spaces",
                        ("Tab Width", ["tab.2", "tab.4", "tab.8"]), "fmt.detect",
                        "fmt.to_spaces", "fmt.to_tabs", "-", "fmt.trim", "fmt.bak",
                        "fmt.autosave", "-",
                        ("Language Mode", ["lang.auto", "lang.text", "-"]
                         + [f"lang.{k}" for k in LANG_NAMES]),
                        "fmt.font", "fmt.ruler_col", "fmt.settings"]),
            ("Encoding", [f"enc.{e}" for e in ENCODINGS] + ["-"]
             + [("Reopen with Encoding", [f"reopen.{e}" for e in ENCODINGS])]
             + [("Line Endings", [f"eol.{n}" for n in EOLS])]),
            ("Tools", [("Case", ["case.upper", "case.lower", "case.title", "-", "case.snake",
                                 "case.camel", "case.pascal", "case.kebab", "case.constant"]),
                       ("Lines", ["lines.sort", "lines.unique", "lines.reverse", "lines.shuffle",
                                  "lines.number", "lines.keep", "lines.remove", "lines.trim",
                                  "lines.align", "lines.wrap"]),
                       ("Clean Up", ["clean.invisible", "clean.quotes", "clean.nfc"]),
                       ("Escape", ["esc.html", "esc.unhtml", "esc.json", "esc.unjson",
                                   "esc.regex"]),
                       ("Data", ["data.json_fmt", "data.json_min", "data.json_sort", "data.xml",
                                 "data.validate", "-", "data.json_tree", "data.csv"]),
                       ("Encode", ["code.b64e", "code.b64d", "code.urle", "code.urld", "-",
                                   "hash.MD5", "hash.SHA-1", "hash.SHA-256", "-", "num.dec",
                                   "num.hex", "num.bin", "num.oct", "time.convert"]),
                       ("Markdown", ["md.bold", "md.italic", "md.toc"]), "-",
                       "tools.calc", "tools.stats", "tools.goal", "tools.pomodoro", "-",
                       "tools.regex", "tools.sql", "tools.http", "tools.hex", "tools.follow",
                       "-",
                       ("Customize", ["custom.snippets", "custom.templates", "custom.keys",
                                      "custom.themes"])]),
            ("Run", ["run.file", "run.selection", "run.tests", "run.profile", "run.stop", "-",
                     "run.preview", "run.clear"]),
            ("Help", ["help.keys", "help.doc", "-", "help.folder", "help.errors", "help.reset",
                      "help.portable", "help.shortcut", "help.selftest", "-", "help.about"]),
        ]

    def _fill_menu(self, menu, items):
        for item in items:
            if item == "-":
                menu.add_separator()
            elif isinstance(item, tuple) and item[0] == "recent":
                self.recent_menu = tk.Menu(menu, tearoff=0)
                menu.add_cascade(label="Open Recent", menu=self.recent_menu)
            elif isinstance(item, tuple):
                sub = tk.Menu(menu, tearoff=0)
                self._fill_menu(sub, item[1])
                menu.add_cascade(label=item[0], menu=sub)
                self.submenus[item[0]] = sub
            else:
                cmd = self.commands[item]
                kw = dict(label=cmd["label"], accelerator=self.accel(item),
                          command=cmd["func"])
                if cmd["kind"] == "check":
                    menu.add_checkbutton(variable=cmd["var"], **kw)
                elif cmd["kind"] == "radio":
                    menu.add_radiobutton(variable=cmd["var"], value=cmd["value"], **kw)
                else:
                    menu.add_command(**kw)

    def close_tabs_right(self, doc=None):
        doc = doc or self.current()
        if not doc:
            return
        docs = self.ordered_docs()
        for other in docs[docs.index(doc) + 1:]:
            if not other.pinned and not self.close_tab(other):
                return
        self.nb.select(doc.frame)

    def _color_image(self, color):
        img = self._tab_images.get(color)
        if img is None:
            img = tk.PhotoImage(master=self.root, width=10, height=10)
            img.put(color, to=(1, 1, 9, 9))
            self._tab_images[color] = img
        return img

    def layout_status(self):
        items = self.status_items
        order = ["zoom", "eol", "enc", "indent", "lang", "counts", "pos", "branch", "goal",
                 "pomodoro", "macro", "vim"]
        wanted = [k for k in order if items[k].cget("text")]
        if wanted == getattr(self, "_status_mapped", None):
            return
        self._status_mapped = wanted
        self.status.pack_forget()
        for label in items.values():
            label.pack_forget()
        for key in wanted:
            items[key].pack(side="right")
        self.status.pack(side="left", fill="x", expand=True)

    def open_virtual(self, name, content, lang=None, read_only=False, select=True):
        cur = self.current()
        doc = cur if cur and cur.is_blank() and select else self.new_tab(select=select)
        doc.display_name = name
        doc.lang_override = lang
        doc.load(None, content, "utf-8", len(content.encode("utf-8")))
        doc.path = None
        if read_only:
            doc.set_read_only(True)
        doc.text.edit_modified(False)
        self.update_tab(doc)
        if select:
            self._on_tab_changed()
        return doc

    def _print(self, doc, content, numbers, header):
        try:
            if sys.platform == "win32":
                lines = content.split("\n")
                digits = len(str(len(lines)))
                body = [f"{i:>{digits}}  {l}" if numbers else l for i, l in enumerate(lines, 1)]
                if header:
                    body = [f"{doc.name()}    {time.strftime('%Y-%m-%d %H:%M')}", ""] + body
                fd, tmp = tempfile.mkstemp(prefix="notepad_", suffix=".txt")
                with os.fdopen(fd, "w", encoding="utf-8-sig", newline="") as f:
                    f.write("\r\n".join(body))
                os.startfile(tmp, "print")
            else:
                fd, tmp = tempfile.mkstemp(prefix="notepad_", suffix=".pdf")
                with os.fdopen(fd, "wb") as f:
                    f.write(build_pdf(content, doc.name(), numbers, header))
                subprocess.run(["lpr", tmp], check=True)
        except (OSError, subprocess.CalledProcessError) as e:
            messagebox.showerror("Error", f"Could not print:\n{e}")
            return
        self.set_message("Sent to printer")

    def add_history_version(self, path, content):
        try:
            folder = os.path.join(HISTORY_DIR, path_key(path))
            os.makedirs(folder, exist_ok=True)
            files = sorted(f for f in os.listdir(folder) if f.endswith(".txt"))
            if files:
                with open(os.path.join(folder, files[-1]), encoding="utf-8") as f:
                    if f.read() == content:
                        return
            stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S-%f")
            with open(os.path.join(folder, stamp + ".txt"), "w", encoding="utf-8",
                      newline="") as f:
                f.write(content)
            write_json_file(os.path.join(folder, "meta.json"), {"path": path})
            for old in files[:max(0, len(files) + 1 - HISTORY_KEEP)]:
                os.remove(os.path.join(folder, old))
        except OSError:
            pass

    def history_versions(self, path):
        folder = os.path.join(HISTORY_DIR, path_key(path))
        try:
            files = sorted((f for f in os.listdir(folder) if f.endswith(".txt")), reverse=True)
        except OSError:
            return []
        return [os.path.join(folder, f) for f in files]

    def local_history(self):
        doc = self.current()
        if not doc or not doc.path:
            messagebox.showinfo(APP, "Local history is kept for files saved on disk.")
            return
        versions = self.history_versions(doc.path)
        if not versions:
            messagebox.showinfo(APP, "There are no saved versions of this file yet.\n"
                                     "A version is stored every time you save.")
            return
        win = tk.Toplevel(self.root)
        win.title(f"Local History - {doc.name()}")
        win.transient(self.root)
        lb = tk.Listbox(win, width=60, height=14, font=self.font, exportselection=False)
        lb.pack(fill="both", expand=True, padx=8, pady=8)
        for path in versions:
            stamp = os.path.basename(path)[:15]
            when = datetime.datetime.strptime(stamp, "%Y%m%d-%H%M%S").strftime(
                "%Y-%m-%d %H:%M:%S")
            lb.insert("end", f"{when}    {format_bytes(os.path.getsize(path))}")
        lb.selection_set(0)

        def chosen():
            sel = lb.curselection()
            if not sel:
                return None
            with open(versions[sel[0]], encoding="utf-8") as f:
                return f.read()

        def compare():
            text = chosen()
            if text is not None:
                self._show_diff("saved version", text, doc.name(), doc.content())

        def restore():
            text = chosen()
            if text is not None and self._editable(doc):
                self.edit_block(doc, doc.text, "1.0", "end-1c", text)
                self.set_message("Version restored. Use Undo to go back.")
                win.destroy()

        def open_copy():
            text = chosen()
            if text is not None:
                stamp = lb.get(lb.curselection()[0]).split("    ")[0]
                self.open_virtual(f"{doc.name()} @ {stamp}", text, doc.lang_override or
                                  detect_language(doc.path), read_only=True)

        buttons = tk.Frame(win)
        buttons.pack(pady=(0, 8))
        for label, func in (("Compare with Current", compare), ("Restore", restore),
                            ("Open", open_copy), ("Close", win.destroy)):
            tk.Button(buttons, text=label, command=func).pack(side="left", padx=4)
        lb.bind("<Double-Button-1>", lambda e: compare())
        win.bind("<Escape>", lambda e: win.destroy())

    def compare_saved(self):
        doc = self.current()
        if not doc or not doc.path:
            messagebox.showinfo(APP, "This document has not been saved to disk.")
            return
        result = self._read(doc.path, doc.encoding)
        if result:
            saved = result[0].replace("\r\n", "\n").replace("\r", "\n")
            self._show_diff(f"{doc.name()} (on disk)", saved, f"{doc.name()} (editor)",
                            doc.content())

    def save_undo_history(self, doc):
        if not doc.path or doc.kind != "text" or len(doc.undo_snaps) < 2:
            return
        try:
            doc._snapshot()
            write_json_file(os.path.join(UNDO_DIR, path_key(doc.path) + ".json"),
                            {"path": doc.path, "snaps": doc.undo_snaps[-UNDO_SNAPSHOTS:]})
        except OSError:
            pass

    def load_undo_history(self, doc):
        if not doc.path:
            return
        data = load_json_file(os.path.join(UNDO_DIR, path_key(doc.path) + ".json"), None)
        if not isinstance(data, dict):
            return
        snaps = data.get("snaps") or []
        if len(snaps) >= 2 and snaps[-1] == doc.content():
            doc.undo_prev = snaps[:-1]
            doc.undo_snaps = list(snaps)

    def undo_previous_session(self):
        doc = self.current()
        if not doc or not self._editable(doc):
            return
        if not doc.undo_prev:
            self.set_message("There are no saved changes from a previous session for this file")
            self.root.bell()
            return
        previous = doc.undo_prev.pop()
        self.edit_block(doc, doc.text, "1.0", "end-1c", previous)
        self.set_message(f"Restored an earlier state ({len(doc.undo_prev)} more available)")

    @staticmethod
    def instance_connect(payload):
        info = load_json_file(INSTANCE_FILE, None)
        if not isinstance(info, dict):
            return False
        try:
            with socket.create_connection(("127.0.0.1", int(info["port"])), timeout=1.5) as s:
                payload = dict(payload, token=info["token"])
                s.sendall(json.dumps(payload).encode("utf-8") + b"\n")
                s.settimeout(3)
                return s.recv(16).startswith(b"OK")
        except (OSError, KeyError, ValueError):
            return False

    def instance_serve(self):
        token = secrets.token_hex(16)
        try:
            server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server.bind(("127.0.0.1", 0))
            server.listen(5)
        except OSError:
            return
        self._server = server
        try:
            write_json_file(INSTANCE_FILE, {"port": server.getsockname()[1], "token": token,
                                            "pid": os.getpid()})
        except OSError:
            pass

        def serve():
            while True:
                try:
                    conn, _ = server.accept()
                except OSError:
                    return
                with conn:
                    try:
                        conn.settimeout(5)
                        data = b""
                        while not data.endswith(b"\n") and len(data) < 50_000_000:
                            chunk = conn.recv(65536)
                            if not chunk:
                                break
                            data += chunk
                        message = json.loads(data.decode("utf-8"))
                        if message.get("token") == token:
                            self._instance_queue.put(message)
                            conn.sendall(b"OK\n")
                    except (OSError, ValueError):
                        pass

        threading.Thread(target=serve, daemon=True).start()
        self.root.after(200, self._instance_poll)

    def _instance_poll(self):
        try:
            while True:
                message = self._instance_queue.get_nowait()
                self.handle_args(message.get("files", []), message.get("stdin"),
                                 message.get("cwd"))
                self.root.deiconify()
                self.root.lift()
                try:
                    self.root.focus_force()
                except tk.TclError:
                    pass
        except queue.Empty:
            pass
        self.root.after(200, self._instance_poll)

    def instance_stop(self):
        if self._server:
            try:
                self._server.close()
            except OSError:
                pass
            info = load_json_file(INSTANCE_FILE, None)
            if isinstance(info, dict) and info.get("pid") == os.getpid():
                try:
                    os.remove(INSTANCE_FILE)
                except OSError:
                    pass
            self._server = None

    @staticmethod
    def parse_file_arg(arg, cwd=None):
        path = arg if os.path.isabs(arg) or not cwd else os.path.join(cwd, arg)
        if os.path.exists(path):
            return path, None, 0
        m = re.match(r"^(.*?):(\d+)(?::(\d+))?$", path)
        if m and os.path.exists(m.group(1)):
            return m.group(1), int(m.group(2)), max(0, int(m.group(3) or 1) - 1)
        return path, None, 0

    def handle_args(self, files, stdin_text=None, cwd=None):
        for arg in files:
            path, line, col = self.parse_file_arg(arg, cwd)
            if os.path.isfile(path):
                self.open_file(path, line=line, col=col)
            elif os.path.isdir(path):
                self.set_explorer_root(path)
            else:
                self.set_message(f"File not found: {path}")
        if stdin_text is not None:
            self.open_virtual("stdin", stdin_text)

    def _auto_save_tick(self):
        if self.auto_save.get():
            for doc in self.docs.values():
                if doc.modified() and doc.kind == "text" and (doc.path or doc.remote):
                    self.save(doc, quiet=True)
        self.root.after(AUTO_SAVE_INTERVAL, self._auto_save_tick)

    def open_image(self, path, doc=None):
        if doc is None:
            cur = self.current()
            doc = cur if cur and cur.is_blank() else self.new_tab()
        doc.kind = "image"
        doc.path = os.path.abspath(path)
        if not self.load_image(doc, path):
            return None
        self.update_tab(doc)
        self._on_tab_changed()
        self._add_recent(doc.path)
        return doc

    def load_image(self, doc, path):
        try:
            source = tk.PhotoImage(master=self.root, file=path)
        except tk.TclError as e:
            messagebox.showerror("Error", f"Could not open image:\n{e}")
            return False
        doc.image_source = source
        doc.image_scale = 1
        try:
            doc.mtime = os.path.getmtime(path)
        except OSError:
            doc.mtime = None
        self.render_image(doc)
        return True

    def render_image(self, doc):
        source = doc.image_source
        scale = doc.image_scale
        if scale > 1:
            image = source.zoom(int(scale))
        elif scale < 1:
            image = source.subsample(int(round(1 / scale)))
        else:
            image = source
        doc.image = image
        t = doc.text
        t.config(state="normal")
        t.delete("1.0", "end")
        t.image_create("1.0", image=image, padx=8, pady=8)
        t.edit_reset()
        t.edit_modified(False)
        t.config(state="disabled")
        doc.read_only = True
        self.set_message(f"{doc.path}   |   {source.width()} x {source.height()} px   |   "
                         f"zoom {int(scale * 100)}%   (Ctrl + mouse wheel to zoom)")

    def open_lazy(self, path, kind):
        cur = self.current()
        doc = cur if cur and cur.is_blank() else self.new_tab()
        doc.kind = "large" if kind == "text" else kind
        doc.path = os.path.abspath(path)
        if kind == "hex":
            doc.display_name = os.path.basename(path) + " [hex]"
        try:
            doc.mtime = os.path.getmtime(path)
            size = os.path.getsize(path)
        except OSError as e:
            messagebox.showerror("Error", f"Could not open file:\n{e}")
            return None
        doc.lazy = {"path": doc.path, "offset": 0, "size": size, "done": False,
                    "decoder": codecs.getincrementaldecoder("utf-8")(errors="replace")}
        doc.text.config(state="normal")
        doc.text.delete("1.0", "end")
        doc.set_read_only(True)
        self.load_more(doc)
        if doc.lazy and not doc.lazy["done"]:
            self.load_more(doc)
        self.update_tab(doc)
        self._on_tab_changed()
        self.set_message(f"{doc.path}   |   {format_bytes(size)}   |   "
                         f"{'Hex view' if kind == 'hex' else 'Large file viewer'} (read-only, "
                         "loads more as you scroll)")
        return doc

    def load_more(self, doc):
        state = doc.lazy
        if not state or state["done"]:
            return
        chunk_size = HEX_CHUNK if doc.kind == "hex" else LARGE_CHUNK
        try:
            with open(state["path"], "rb") as f:
                f.seek(state["offset"])
                data = f.read(chunk_size)
        except OSError:
            state["done"] = True
            return
        if doc.kind == "hex":
            text = "\n".join(hex_lines(data, state["offset"]))
        else:
            text = state["decoder"].decode(data, final=len(data) < chunk_size)
            text = text.replace("\r\n", "\n").replace("\r", "\n")
        start_offset = state["offset"]
        state["offset"] += len(data)
        if len(data) < chunk_size or state["offset"] >= state["size"]:
            state["done"] = True
        t = doc.text
        t.config(state="normal")
        if start_offset and doc.kind == "hex" and text:
            text = "\n" + text
        t.insert("end-1c", text)
        t.edit_reset()
        t.edit_modified(False)
        t.config(state="disabled")
        doc.schedule_refresh(100)

    def toggle_follow(self):
        doc = self.current()
        if not doc or not doc.path or doc.kind != "text":
            messagebox.showinfo(APP, "Follow mode works with text files saved on disk.")
            return
        if doc.follow:
            if doc.follow.get("job"):
                doc.text.after_cancel(doc.follow["job"])
            doc.follow = None
            self.set_message("Follow mode off")
            return
        if doc.modified() and not messagebox.askyesno(
                APP, "Follow mode reloads the file and makes it read-only.\nDiscard unsaved "
                     "changes?"):
            return
        self.reload(doc, ask=False)
        doc.set_read_only(True)
        doc.follow = {"offset": os.path.getsize(doc.path), "job": None,
                      "decoder": codecs.getincrementaldecoder(doc.encoding or "utf-8")(
                          errors="replace")}
        doc.text.see("end")
        self.set_message("Following file: new lines appear automatically")
        self._follow_tick(doc)

    def _follow_tick(self, doc):
        state = doc.follow
        if not state or str(doc.frame) not in self.docs:
            return
        try:
            size = os.path.getsize(doc.path)
        except OSError:
            size = state["offset"]
        if size < state["offset"]:
            doc.follow = None
            self.reload(doc, ask=False)
            doc.set_read_only(True)
            state["offset"] = size
            doc.follow = state
        elif size > state["offset"]:
            with open(doc.path, "rb") as f:
                f.seek(state["offset"])
                data = f.read(size - state["offset"])
            state["offset"] = size
            text = state["decoder"].decode(data).replace("\r\n", "\n").replace("\r", "\n")
            t = doc.text
            at_end = t.yview()[1] > 0.999
            t.config(state="normal")
            t.insert("end-1c", text)
            t.edit_modified(False)
            t.config(state="disabled")
            if doc.filter_pattern:
                self.apply_filter(doc, doc.filter_pattern)
            if at_end:
                t.see("end")
            doc.mtime = os.path.getmtime(doc.path)
        state["job"] = doc.text.after(1000, self._follow_tick, doc)

    def view_as_hex(self):
        doc = self.current()
        if not doc or not doc.path:
            path = filedialog.askopenfilename(title="Open File in Hex Viewer")
            if not path:
                return
        else:
            path = doc.path
        self.open_lazy(path, "hex")

    def open_scratchpad(self):
        for doc in self.docs.values():
            if doc.scratch:
                self.nb.select(doc.frame)
                return doc
        try:
            os.makedirs(CONFIG_DIR, exist_ok=True)
            if not os.path.exists(SCRATCH_FILE):
                with open(SCRATCH_FILE, "w", encoding="utf-8") as f:
                    f.write("")
        except OSError as e:
            messagebox.showerror("Error", f"Could not create the scratchpad:\n{e}")
            return None
        result = self._read(SCRATCH_FILE, "utf-8")
        if result is None:
            return None
        cur = self.current()
        doc = cur if cur and cur.is_blank() else self.new_tab()
        doc.scratch = True
        doc.load(SCRATCH_FILE, result[0], "utf-8", result[2])
        doc.display_name = "Scratchpad"
        doc.lang_override = "markdown"
        doc.setup_language()
        self.update_tab(doc)
        self._on_tab_changed()
        return doc

    def save_scratch(self, doc):
        if not doc.modified():
            return
        try:
            with open(SCRATCH_FILE, "w", encoding="utf-8", newline="") as f:
                f.write(doc.content())
            doc.mtime = os.path.getmtime(SCRATCH_FILE)
            doc.text.edit_modified(False)
        except OSError:
            pass

    def new_from_template(self):
        templates = dict(TEMPLATES)
        try:
            for name in sorted(os.listdir(TEMPLATES_DIR)):
                full = os.path.join(TEMPLATES_DIR, name)
                if os.path.isfile(full):
                    with open(full, encoding="utf-8", errors="replace") as f:
                        templates[f"{name} (custom)"] = (os.path.splitext(name)[1], f.read())
        except OSError:
            pass
        names = list(templates)
        win = tk.Toplevel(self.root)
        win.title("New from Template")
        win.transient(self.root)
        lb = tk.Listbox(win, width=40, height=min(16, len(names)), exportselection=False)
        lb.pack(padx=8, pady=8, fill="both", expand=True)
        for name in names:
            lb.insert("end", name)
        lb.selection_set(0)

        def create(event=None):
            sel = lb.curselection()
            if not sel:
                return
            name = names[sel[0]]
            ext, content = templates[name]
            win.destroy()
            doc = self.new_tab()
            doc.lang_override = detect_language("x" + ext)
            doc.text.insert("1.0", content)
            doc.text.edit_reset()
            doc.setup_language()
            doc.default_ext = ext
            self.update_tab(doc)
            self._on_tab_changed()

        lb.bind("<Double-Button-1>", create)
        lb.bind("<Return>", create)
        tk.Label(win, text=f"Add your own templates to: {TEMPLATES_DIR}", fg="gray").pack(
            padx=8, anchor="w")
        buttons = tk.Frame(win)
        buttons.pack(pady=8)
        tk.Button(buttons, text="Create", width=10, command=create).pack(side="left", padx=4)
        tk.Button(buttons, text="Cancel", width=10, command=win.destroy).pack(side="left", padx=4)
        win.bind("<Escape>", lambda e: win.destroy())
        lb.focus_set()

    def open_templates_folder(self):
        os.makedirs(TEMPLATES_DIR, exist_ok=True)
        reveal_in_file_manager(TEMPLATES_DIR)

    def open_ftp(self):
        win = tk.Toplevel(self.root)
        win.title("Open from FTP")
        win.transient(self.root)
        win.resizable(False, False)
        last = self.cfg.get("ftp", {})
        fields = {}
        for row, (key, label, default) in enumerate((
                ("host", "Host:", last.get("host", "")), ("port", "Port:", last.get("port", "21")),
                ("user", "User:", last.get("user", "anonymous")), ("password", "Password:", ""),
                ("path", "Remote file:", last.get("path", "/")))):
            tk.Label(win, text=label).grid(row=row, column=0, sticky="e", padx=6, pady=3)
            var = tk.StringVar(value=default)
            tk.Entry(win, textvariable=var, width=40,
                     show="*" if key == "password" else "").grid(row=row, column=1, padx=6,
                                                                pady=3)
            fields[key] = var
        tls = tk.BooleanVar(value=bool(last.get("tls")))
        tk.Checkbutton(win, text="Use TLS (FTPS)", variable=tls).grid(row=5, column=1, sticky="w")

        def go():
            info = {k: v.get().strip() for k, v in fields.items()}
            info["tls"] = tls.get()
            if not info["host"] or not info["path"]:
                return
            self.cfg["ftp"] = {k: v for k, v in info.items() if k != "password"}
            win.destroy()
            self.load_ftp(info)

        buttons = tk.Frame(win)
        buttons.grid(row=6, column=0, columnspan=2, pady=8)
        tk.Button(buttons, text="Open", width=10, command=go).pack(side="left", padx=4)
        tk.Button(buttons, text="Cancel", width=10, command=win.destroy).pack(side="left", padx=4)
        win.bind("<Return>", lambda e: go())
        win.bind("<Escape>", lambda e: win.destroy())

    def _ftp_connect(self, info):
        ftp = ftplib.FTP_TLS() if info.get("tls") else ftplib.FTP()
        ftp.connect(info["host"], int(info.get("port") or 21), timeout=20)
        ftp.login(info.get("user") or "anonymous", info.get("password") or "")
        if info.get("tls"):
            ftp.prot_p()
        return ftp

    def load_ftp(self, info):
        try:
            ftp = self._ftp_connect(info)
            buf = io.BytesIO()
            ftp.retrbinary(f"RETR {info['path']}", buf.write)
            ftp.quit()
        except (OSError, ftplib.all_errors, ValueError) as e:
            messagebox.showerror("FTP", f"Could not download the file:\n{e}")
            return None
        data = buf.getvalue()
        content, enc = decode_bytes(data)
        name = f"ftp://{info['host']}{info['path'] if info['path'].startswith('/') else '/' + info['path']}"
        doc = self.open_virtual(name, content, detect_language(info["path"]))
        doc.encoding = enc
        doc.remote = info
        doc.eol = detect_eol(content)
        self.update_tab(doc)
        self.set_message(f"Downloaded {name} ({format_bytes(len(data))}). Save uploads it back.")
        return doc

    def save_ftp(self, doc):
        content = doc.content()
        if doc.eol != "\n":
            content = content.replace("\n", doc.eol)
        try:
            data = content.encode(doc.encoding)
            ftp = self._ftp_connect(doc.remote)
            ftp.storbinary(f"STOR {doc.remote['path']}", io.BytesIO(data))
            ftp.quit()
        except UnicodeEncodeError as e:
            messagebox.showerror("Error", f"The text cannot be stored as {doc.encoding}:\n{e}")
            return False
        except (OSError, ftplib.all_errors, ValueError) as e:
            messagebox.showerror("FTP", f"Could not upload the file:\n{e}")
            return False
        doc.text.edit_modified(False)
        self.update_tab(doc)
        self.set_message(f"Uploaded {doc.display_name}")
        return True

    def open_archive(self, path=None):
        if not path:
            path = filedialog.askopenfilename(title="Open Archive",
                                              filetypes=[("All files", "*.*"),
                                                         ("Zip archives", "*.zip *.jar *.whl "
                                                          "*.epub *.docx *.xlsx")])
            if not path:
                return
        try:
            archive = zipfile.ZipFile(path)
            infos = [i for i in archive.infolist() if not i.is_dir()]
        except (OSError, zipfile.BadZipFile) as e:
            messagebox.showerror("Error", f"Could not open the archive:\n{e}")
            return
        win = tk.Toplevel(self.root)
        win.title(f"Archive - {os.path.basename(path)}")
        win.geometry("700x450")
        tree = ttk.Treeview(win, columns=("size", "date"), selectmode="browse")
        tree.heading("#0", text="Name")
        tree.heading("size", text="Size")
        tree.heading("date", text="Modified")
        tree.column("size", width=100, anchor="e")
        tree.column("date", width=140)
        sb = ttk.Scrollbar(win, command=tree.yview)
        tree.config(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        tree.pack(fill="both", expand=True)
        nodes = {"": ""}
        for info in sorted(infos, key=lambda i: i.filename):
            parts = info.filename.split("/")
            parent = ""
            for i, part in enumerate(parts[:-1]):
                key = "/".join(parts[:i + 1])
                if key not in nodes:
                    nodes[key] = tree.insert(nodes[parent], "end", text=part + "/", open=False)
                parent = key
            date = "%04d-%02d-%02d %02d:%02d" % info.date_time[:5]
            tree.insert(nodes[parent], "end", iid="f:" + info.filename, text=parts[-1],
                        values=(format_bytes(info.file_size), date))
        label = tk.Label(win, anchor="w", text=f"{len(infos)} files. Double-click a file to open "
                                                "it (read-only).")
        label.pack(fill="x", padx=6, pady=4)

        def open_entry(event=None):
            sel = tree.selection()
            if not sel or not sel[0].startswith("f:"):
                return
            name = sel[0][2:]
            try:
                data = archive.read(name)
            except (OSError, zipfile.BadZipFile, KeyError) as e:
                messagebox.showerror("Error", str(e))
                return
            if looks_binary(data):
                messagebox.showinfo(APP, "This entry is binary and cannot be shown as text.")
                return
            text, enc = decode_bytes(data)
            doc = self.open_virtual(f"{os.path.basename(path)}/{name}", text,
                                    detect_language(name), read_only=True)
            doc.encoding = enc

        def extract():
            sel = tree.selection()
            if not sel or not sel[0].startswith("f:"):
                return
            name = sel[0][2:]
            target = filedialog.asksaveasfilename(parent=win, initialfile=os.path.basename(name))
            if target:
                with open(target, "wb") as f:
                    f.write(archive.read(name))
                self.set_message(f"Extracted to {target}")

        tree.bind("<Double-Button-1>", open_entry)
        tree.bind("<Return>", open_entry)
        tk.Button(win, text="Extract Selected...", command=extract).pack(side="left", padx=6,
                                                                         pady=6)
        win.protocol("WM_DELETE_WINDOW", lambda: (archive.close(), win.destroy()))

    def _build_find_bar(self):
        bar = tk.Frame(self.root, bd=0)
        self.find_bar = bar
        tk.Label(bar, text="Find:").pack(side="left", padx=(8, 2), pady=3)
        self.find_entry_bar = tk.Entry(bar, textvariable=self.find_var, width=32, bd=1,
                                       relief="solid")
        self.find_entry_bar.pack(side="left", padx=2, pady=3)
        for text, func in (("▲", self.find_prev), ("▼", self.find_next)):
            tk.Button(bar, text=text, bd=0, padx=6, command=func).pack(side="left")
        self.find_bar_checks = []
        for text, var in (("Aa", self.opt_case), ("Word", self.opt_word), (".*", self.opt_regex)):
            cb = tk.Checkbutton(bar, text=text, variable=var, command=self._find_bar_changed)
            cb.pack(side="left", padx=2)
            self.find_bar_checks.append(cb)
        self.find_count = tk.Label(bar, text="", padx=8)
        self.find_count.pack(side="left")
        tk.Button(bar, text="Replace...", bd=0, padx=6,
                  command=lambda: self.show_find(True)).pack(side="left")
        tk.Button(bar, text="✕", bd=0, padx=8, command=self.hide_find_bar).pack(side="right")
        e = self.find_entry_bar
        e.bind("<Return>", lambda ev: (self.find_next(), "break")[1])
        e.bind("<Shift-Return>", lambda ev: (self.find_prev(), "break")[1])
        e.bind("<Escape>", lambda ev: (self.hide_find_bar(), "break")[1])
        e.bind("<F3>", lambda ev: (self.find_next(), "break")[1])
        e.bind("<Shift-F3>", lambda ev: (self.find_prev(), "break")[1])
        self.find_var.trace_add("write", lambda *a: self._find_bar_changed())

    def show_find_bar(self):
        doc, w = self.cv()
        if doc and w.tag_ranges("sel"):
            selected = w.get("sel.first", "sel.last")
            if selected and "\n" not in selected and len(selected) < 200:
                self.find_var.set(selected)
        if not self.find_bar_visible:
            self.find_bar.pack(side="bottom", fill="x", before=self.hpane)
            self.find_bar_visible = True
        self.find_entry_bar.focus_set()
        self.find_entry_bar.select_range(0, "end")
        self._find_bar_changed()

    def hide_find_bar(self):
        if self.find_bar_visible:
            self.find_bar.pack_forget()
            self.find_bar_visible = False
        for doc in self.docs.values():
            doc.text.tag_remove("find_all", "1.0", "end")
        doc, w = self.cv()
        if w:
            w.focus_set()

    def _find_bar_changed(self):
        if self._find_job:
            self.root.after_cancel(self._find_job)
        self._find_job = self.root.after(120, self._find_highlight_all)

    def _find_highlight_all(self):
        self._find_job = None
        doc, w = self.cv()
        if not doc:
            return
        t = doc.text
        t.tag_remove("find_all", "1.0", "end")
        if not self.find_bar_visible:
            return
        term = self.find_var.get()
        if not term:
            self.find_count.config(text="")
            return
        pattern = self._pattern()
        if not pattern:
            self.find_count.config(text="invalid")
            return
        content = doc.content()
        index = make_indexer(content)
        matches = [m for m in pattern.finditer(content) if m.end() > m.start()]
        ranges = []
        for m in matches[:FIND_ALL_LIMIT]:
            ranges.extend((index(m.start()), index(m.end())))
        for i in range(0, len(ranges), 2000):
            t.tag_add("find_all", *ranges[i:i + 2000])
        current = 0
        sel = w.tag_ranges("sel")
        if sel:
            start = self._offset(w, sel[0])
            for i, m in enumerate(matches, 1):
                if m.start() == start:
                    current = i
                    break
        total = len(matches)
        if not total:
            self.find_count.config(text="No results")
        elif current:
            self.find_count.config(text=f"{current} of {total:,}")
        else:
            self.find_count.config(text=f"{total:,} results")

    def push_nav(self, doc, index):
        entry = (doc.id, index)
        if self.nav_back and self.nav_back[-1] == entry:
            return
        self.nav_back.append(entry)
        del self.nav_back[:-100]
        self.nav_fwd.clear()

    def _nav_jump(self, entry):
        doc_id, index = entry
        doc = next((d for d in self.docs.values() if d.id == doc_id), None)
        if not doc:
            return False
        self.nb.select(doc.frame)
        line, col = index.split(".")
        self._goto(doc, int(line), int(col), record=False)
        return True

    def nav_go_back(self):
        doc, w = self.cv()
        while self.nav_back:
            entry = self.nav_back.pop()
            if doc:
                self.nav_fwd.append((doc.id, w.index("insert")))
            if self._nav_jump(entry):
                return
        self.set_message("No earlier position")

    def nav_go_forward(self):
        doc, w = self.cv()
        while self.nav_fwd:
            entry = self.nav_fwd.pop()
            if doc:
                self.nav_back.append((doc.id, w.index("insert")))
            if self._nav_jump(entry):
                return
        self.set_message("No later position")

    def after_doc_refresh(self, doc, content):
        if doc.kind == "text" and len(content) <= HIGHLIGHT_LIMIT:
            doc.symbols = find_symbols(content, doc.lang) if doc.lang else []
        else:
            doc.symbols = []
        if doc.scratch:
            self.save_scratch(doc)
        if doc.md_text:
            doc.update_md_preview(content)
        if doc.git_base is not None:
            self.git_marks(doc, content)
        if self.current() is doc:
            self.refresh_outline()
            self.update_status()

    def _console_write(self, text, tag=None):
        self.console_text.insert("end", text, tag or ())
        self.console_text.see("end")

    def _console_prompt(self, prompt):
        self._console_write(prompt, "prompt")
        self.console_text.mark_set("console_input", "end-1c")
        self.console_text.mark_gravity("console_input", "left")
        self.console_text.mark_set("insert", "end-1c")

    def _console_key(self, event):
        c = self.console_text
        if event.char and event.char.isprintable() and not (event.state & 0x4):
            if c.compare("insert", "<", "console_input"):
                c.mark_set("insert", "end-1c")
        return None

    def _console_backspace(self, event):
        c = self.console_text
        if c.tag_ranges("sel") and c.compare("sel.first", ">=", "console_input"):
            return None
        if c.compare("insert", "<=", "console_input"):
            return "break"
        return None

    def _console_history(self, step):
        if not self.console_history:
            return "break"
        self.console_hpos = max(0, min(len(self.console_history),
                                       self.console_hpos + step))
        line = (self.console_history[self.console_hpos]
                if self.console_hpos < len(self.console_history) else "")
        c = self.console_text
        c.delete("console_input", "end-1c")
        c.insert("console_input", line)
        c.mark_set("insert", "end-1c")
        return "break"

    def _console_enter(self, event=None):
        c = self.console_text
        line = c.get("console_input", "end-1c")
        c.mark_set("insert", "end-1c")
        self._console_write("\n")
        if line.strip():
            self.console_history.append(line)
        self.console_hpos = len(self.console_history)
        out = io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(out):
            more = self.console.push(line)
        text = out.getvalue()
        if text:
            self._console_write(text, "error" if "Traceback" in text or "Error" in text
                                else None)
        self._console_prompt("... " if more else ">>> ")
        return "break"

    def show_console(self):
        self.show_output()
        self.bottom_nb.select(self.console_frame)
        self.console_text.focus_set()
        self.console_text.mark_set("insert", "end-1c")

    def _on_tab_right_click(self, event):
        tab = self._tab_at(event)
        if not tab or tab not in self.docs:
            return
        doc = self.docs[tab]
        m = self.tab_menu
        m.delete(0, "end")
        m.add_command(label="Close", command=lambda: self.close_tab(doc))
        m.add_command(label="Close Others", command=lambda: self.close_other_tabs(doc))
        m.add_command(label="Close Tabs to the Right", command=lambda: self.close_tabs_right(doc))
        m.add_separator()
        m.add_command(label="Unpin Tab" if doc.pinned else "Pin Tab",
                      command=lambda: self.toggle_pin(doc))
        colors = tk.Menu(m, tearoff=0)
        for name, color in (("None", None), ("Red", "#E05252"), ("Orange", "#E8943A"),
                            ("Yellow", "#E5C22E"), ("Green", "#4CAF50"), ("Blue", "#3D8BFD"),
                            ("Purple", "#9C5BD9")):
            colors.add_command(label=name, command=lambda c=color: self.set_tab_color(doc, c))
        m.add_cascade(label="Tab Color", menu=colors)
        m.add_separator()
        state = "normal" if doc.path else "disabled"
        m.add_command(label="Copy Path", state=state, command=lambda: self.copy_path(doc))
        m.add_command(label="Copy File Name", command=lambda: self._copy(doc.name()))
        m.add_command(label="Open Containing Folder", state=state,
                      command=lambda: self.reveal_file(doc))
        m.add_command(label="Rename File...", state=state, command=lambda: self.rename_file(doc))
        m.add_command(label="Duplicate File...", command=lambda: self.duplicate_file(doc))
        m.add_command(label="Move to New Window", state=state,
                      command=lambda: self.move_to_new_window(doc))
        try:
            m.tk_popup(event.x_root, event.y_root)
        finally:
            m.grab_release()
        return "break"

    def toggle_pin(self, doc):
        doc.pinned = not doc.pinned
        if doc.pinned:
            pinned = sum(1 for d in self.ordered_docs() if d.pinned and d is not doc)
            self.nb.insert(pinned, doc.frame)
        self.update_tab(doc)

    def set_tab_color(self, doc, color):
        doc.tab_color = color
        self.update_tab(doc)

    def _copy(self, text):
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        self.set_message("Copied to the clipboard")

    def copy_path(self, doc=None):
        doc = doc or self.current()
        if doc and (doc.path or doc.display_name):
            self._copy(doc.path or doc.display_name)

    def reveal_file(self, doc=None):
        doc = doc or self.current()
        if doc and doc.path:
            try:
                reveal_in_file_manager(doc.path)
            except OSError as e:
                messagebox.showerror("Error", str(e))

    def rename_file(self, doc=None):
        doc = doc or self.current()
        if not doc or not doc.path or doc.scratch:
            messagebox.showinfo(APP, "Save the file first.")
            return
        new = simpledialog.askstring("Rename File", "New name:", initialvalue=doc.name(),
                                     parent=self.root)
        if not new or new == doc.name():
            return
        target = os.path.join(os.path.dirname(doc.path), new)
        if os.path.exists(target):
            messagebox.showerror("Error", f"{new} already exists.")
            return
        try:
            os.rename(doc.path, target)
        except OSError as e:
            messagebox.showerror("Error", f"Could not rename:\n{e}")
            return
        self._remove_recent(doc.path)
        doc.path = os.path.abspath(target)
        doc.mtime = os.path.getmtime(doc.path)
        doc.setup_language()
        self._add_recent(doc.path)
        self.update_tab(doc)
        self.set_message(f"Renamed to {doc.path}")

    def duplicate_file(self, doc=None):
        doc = doc or self.current()
        if not doc or doc.kind != "text":
            return
        base, ext = os.path.splitext(doc.name())
        path = filedialog.asksaveasfilename(
            title="Duplicate As", initialfile=f"{base} copy{ext}",
            initialdir=os.path.dirname(doc.path) if doc.path else None)
        if not path:
            return
        content = doc.content()
        try:
            with open(path, "wb") as f:
                f.write((content.replace("\n", doc.eol) if doc.eol != "\n" else content)
                        .encode(doc.encoding, errors="replace"))
        except OSError as e:
            messagebox.showerror("Error", f"Could not save file:\n{e}")
            return
        self.open_file(path)

    def move_to_new_window(self, doc=None):
        doc = doc or self.current()
        if not doc or not doc.path or doc.kind != "text" or doc.scratch:
            messagebox.showinfo(APP, "Only files saved on disk can be moved to a new window.")
            return
        if doc.modified() and not self.save(doc):
            return
        try:
            cmd = self.relaunch_command("--new-window", doc.path)
            if not cmd:
                return
            subprocess.Popen(cmd)
        except OSError as e:
            messagebox.showerror("Error", str(e))
            return
        doc.pinned = False
        self.close_tab(doc)

    def side_by_side(self):
        doc = self.current()
        others = [d for d in self.ordered_docs() if d is not doc and d.kind == "text"]
        if not doc or not others:
            messagebox.showinfo(APP, "Open at least two text documents first.")
            return
        names = [d.path or d.name() for d in others]
        pick = tk.Toplevel(self.root)
        pick.title("Side by Side With...")
        pick.transient(self.root)
        lb = tk.Listbox(pick, width=60, height=min(12, len(names)), exportselection=False)
        lb.pack(padx=8, pady=8)
        for n in names:
            lb.insert("end", n)
        lb.selection_set(0)

        def go(event=None):
            sel = lb.curselection()
            if sel:
                pick.destroy()
                self._open_side_by_side(doc, others[sel[0]])

        lb.bind("<Double-Button-1>", go)
        lb.bind("<Return>", go)
        tk.Button(pick, text="Open", width=10, command=go).pack(pady=(0, 8))
        lb.focus_set()

    def _open_side_by_side(self, left, right):
        win = tk.Toplevel(self.root)
        win.title(f"{left.name()}  |  {right.name()}")
        win.geometry("1100x650")
        sync = tk.BooleanVar(value=True)
        top = tk.Frame(win)
        top.pack(fill="x")
        tk.Checkbutton(top, text="Synchronized scrolling", variable=sync).pack(side="left",
                                                                              padx=6)
        tk.Label(top, text="Edits here change the documents in the main window.",
                 fg="gray").pack(side="left", padx=12)
        pane = tk.PanedWindow(win, orient="horizontal", sashwidth=6)
        pane.pack(fill="both", expand=True)
        views = []
        busy = [False]
        th = self.theme
        for doc in (left, right):
            frame = tk.Frame(pane)
            tk.Label(frame, text=doc.name(), anchor="w").pack(fill="x")
            body = tk.Frame(frame)
            body.pack(fill="both", expand=True)
            peer = PeerText(body, doc.text, **doc.text_options())
            peer.on_change = doc._on_change
            peer.on_cursor = None
            peer.config(bg=th["bg"], fg=th["fg"], insertbackground=th["cursor"],
                        selectbackground=th["sel_bg"], selectforeground=th["sel_fg"])
            sb = tk.Scrollbar(body, command=peer.yview)
            sb.pack(side="right", fill="y")
            peer.pack(side="left", fill="both", expand=True)
            views.append((peer, sb))
            pane.add(frame, stretch="always")

        def make_scroll(i):
            def on_scroll(first, last):
                views[i][1].set(first, last)
                if sync.get() and not busy[0]:
                    busy[0] = True
                    try:
                        views[1 - i][0].yview_moveto(first)
                    finally:
                        busy[0] = False
            return on_scroll

        for i, (peer, sb) in enumerate(views):
            peer.config(yscrollcommand=make_scroll(i))
        win.update_idletasks()
        try:
            pane.sash_place(0, pane.winfo_width() // 2, 0)
        except tk.TclError:
            pass

    def toggle_md_preview(self):
        doc = self.current()
        if not doc or doc.kind != "text":
            return
        if doc.lang != "markdown" and not doc.md_pane:
            if not messagebox.askyesno(APP, "This document is not Markdown. Show the preview "
                                            "pane anyway?"):
                return
        doc.toggle_md_preview()

    def toggle_minimap(self):
        for doc in self.docs.values():
            if self.show_minimap.get():
                doc.minimap.grid()
                doc.schedule_minimap()
            else:
                doc.minimap.grid_remove()
        self.save_config()

    def set_language_mode(self):
        doc = self.current()
        if not doc:
            return
        value = self.lang_var.get()
        doc.lang_override = None if value == "auto" else value
        doc.setup_language()
        self.update_status()

    def set_indent_style(self):
        doc = self.current()
        if doc:
            doc.indent_spaces = self.use_spaces.get()
            doc.indent_width = self.tab_width.get()
            doc.apply_options()
        self.update_status()
        self.save_config()

    def convert_indent(self, to_spaces):
        doc = self.current()
        if not doc:
            return
        width = doc.indent_width

        def conv(text):
            out = []
            for line in text.split("\n"):
                lead = line[:len(line) - len(line.lstrip(" \t"))]
                cols = len(lead.expandtabs(width))
                new = " " * cols if to_spaces else "\t" * (cols // width) + " " * (cols % width)
                out.append(new + line[len(lead):])
            return "\n".join(out)

        self._transform(conv, "text", "Indentation converted")
        doc.indent_spaces = to_spaces
        self.use_spaces.set(to_spaces)
        doc.apply_options()
        self.update_status()

    def set_ruler_column(self):
        col = simpledialog.askinteger("Ruler Column", "Column for the ruler and long lines:",
                                      initialvalue=self.ruler_col.get(), minvalue=20,
                                      maxvalue=400, parent=self.root)
        if col:
            self.ruler_col.set(col)
            self.refresh_decorations()

    def load_user_themes(self):
        themes = {name: complete_theme(th) for name, th in THEMES.items()}
        data = load_json_file(THEMES_FILE, {})
        if isinstance(data, dict):
            for name, values in data.items():
                if not isinstance(values, dict):
                    continue
                clean = {}
                for key, value in values.items():
                    if key == "rainbow":
                        clean[key] = value if isinstance(value, list) else str(value).split()
                        continue
                    try:
                        r, g, b = self.root.winfo_rgb(str(value))
                        clean[key] = f"#{r // 257:02X}{g // 257:02X}{b // 257:02X}"
                    except tk.TclError:
                        pass
                themes[str(name)] = complete_theme(clean)
        self.themes = themes

    def resolve_theme_name(self):
        name = self.theme_var.get()
        if name == "Auto":
            return "Dark" if os_dark_mode() else "Light"
        return name if name in self.themes else "Blue"

    def _auto_theme_tick(self):
        self._theme_auto_job = None
        if self.theme_var.get() != "Auto":
            return
        if self.themes[self.resolve_theme_name()] is not self.theme:
            self.set_theme()
        self._theme_auto_job = self.root.after(60_000, self._auto_theme_tick)

    def edit_themes(self):
        if not os.path.exists(THEMES_FILE):
            sample = {"My Theme": {
                "bg": "#282A36", "fg": "#F8F8F2", "sel_bg": "#44475A", "sel_fg": "#F8F8F2",
                "cursor": "#F8F8F0", "gutter_bg": "#21222C", "gutter_fg": "#6272A4",
                "status_bg": "#6272A4", "status_fg": "#F8F8F2", "comment": "#6272A4",
                "string": "#F1FA8C", "number": "#BD93F9", "keyword": "#FF79C6",
                "builtin": "#8BE9FD", "function": "#50FA7B", "klass": "#8BE9FD",
                "decorator": "#FFB86C"}}
            try:
                write_json_file(THEMES_FILE, sample)
            except OSError as e:
                messagebox.showerror("Error", str(e))
                return
        self.open_file(THEMES_FILE)
        self.set_message("Edit the themes and save the file to apply them. Missing colors are "
                         "filled in automatically.")

    def edit_keybindings(self):
        defaults = {cid: cmd["keys"] for cid, cmd in self.commands.items()
                    if not cid.startswith(("theme.", "scale.", "lang.", "enc.", "reopen.",
                                           "eol.", "tab."))}
        current = load_json_file(KEYBINDINGS_FILE, None)
        if not isinstance(current, dict):
            try:
                write_json_file(KEYBINDINGS_FILE, defaults)
            except OSError as e:
                messagebox.showerror("Error", str(e))
                return
        self.open_file(KEYBINDINGS_FILE)
        self.set_message('Use Tk key names, e.g. "<Control-Shift-K>". An empty list removes a '
                         "shortcut. Save to apply.")

    def settings_window(self):
        win = tk.Toplevel(self.root)
        win.title("Settings")
        win.transient(self.root)
        nb = ttk.Notebook(win)
        nb.pack(fill="both", expand=True, padx=8, pady=8)

        def page(title):
            f = tk.Frame(nb, padx=10, pady=8)
            nb.add(f, text=title)
            return f

        def checks(frame, ids):
            for cid in ids:
                cmd = self.commands[cid]
                tk.Checkbutton(frame, text=cmd["label"], variable=cmd["var"],
                               command=cmd["func"]).pack(anchor="w")

        editor = page("Editor")
        row = tk.Frame(editor)
        row.pack(anchor="w", pady=(0, 6))
        tk.Label(row, text="Font:").pack(side="left")
        font_label = tk.Label(row, text=f"{self.font.cget('family')} {self.font_size}pt")
        font_label.pack(side="left", padx=6)

        def pick_font():
            self.choose_font()

        tk.Button(row, text="Change...", command=pick_font).pack(side="left")
        row = tk.Frame(editor)
        row.pack(anchor="w", pady=(0, 6))
        tk.Label(row, text="Tab width:").pack(side="left")
        for n in (2, 4, 8):
            tk.Radiobutton(row, text=str(n), value=n, variable=self.tab_width,
                           command=self.set_indent_style).pack(side="left")
        tk.Label(row, text="   Ruler column:").pack(side="left")
        spin = tk.Spinbox(row, from_=20, to=400, width=5, textvariable=self.ruler_col,
                          command=self.refresh_decorations)
        spin.pack(side="left")
        checks(editor, ["fmt.wrap", "fmt.auto_indent", "fmt.auto_close", "fmt.spaces",
                        "fmt.detect", "edit.vim"])
        view = page("Display")
        row = tk.Frame(view)
        row.pack(anchor="w", pady=(0, 6))
        tk.Label(row, text="Theme:").pack(side="left")
        names = ["Auto"] + list(self.themes)
        combo = ttk.Combobox(row, values=names, textvariable=self.theme_var, state="readonly",
                             width=18)
        combo.pack(side="left", padx=6)
        combo.bind("<<ComboboxSelected>>", lambda e: self.set_theme())
        tk.Label(row, text="Interface scale:").pack(side="left", padx=(12, 0))
        scale = ttk.Combobox(row, values=["100", "125", "150", "175", "200"],
                             textvariable=self.ui_scale, state="readonly", width=6)
        scale.pack(side="left", padx=6)
        scale.bind("<<ComboboxSelected>>", lambda e: self.apply_ui_scale())
        checks(view, ["view.line_numbers", "view.highlight", "view.curline", "view.occurrences",
                      "view.rainbow", "view.swatches", "view.guides", "view.whitespace",
                      "view.trailing", "view.long", "view.ruler", "view.minimap",
                      "view.typewriter", "view.focus"])
        files = page("Files")
        checks(files, ["file.restore_session", "file.single_instance", "fmt.autosave",
                       "fmt.bak", "fmt.trim"])
        tk.Label(files, text=f"Local history keeps the last {HISTORY_KEEP} saved versions of "
                             "each file.", fg="gray").pack(anchor="w", pady=(8, 0))
        adv = page("Advanced")
        for label, func in (("Edit Keybindings", self.edit_keybindings),
                            ("Edit Themes", self.edit_themes),
                            ("Edit Snippets", self.edit_snippets),
                            ("Open Templates Folder", self.open_templates_folder),
                            ("Open Settings Folder", self.open_settings_folder),
                            ("Portable Mode...", self.toggle_portable),
                            ("Reset Settings...", self.reset_settings)):
            tk.Button(adv, text=label, width=24, command=func).pack(anchor="w", pady=2)
        tk.Label(adv, text=f"Settings folder: {CONFIG_DIR}", fg="gray").pack(anchor="w",
                                                                            pady=(8, 0))
        tk.Button(win, text="Close", width=10, command=win.destroy).pack(pady=(0, 8))
        win.bind("<Escape>", lambda e: win.destroy())

    def shortcuts_window(self):
        win = tk.Toplevel(self.root)
        win.title("Keyboard Shortcuts")
        win.geometry("640x560")
        query = tk.StringVar()
        top = tk.Frame(win)
        top.pack(fill="x", padx=8, pady=6)
        tk.Label(top, text="Search:").pack(side="left")
        entry = tk.Entry(top, textvariable=query)
        entry.pack(side="left", fill="x", expand=True, padx=4)
        tree = ttk.Treeview(win, columns=("command", "keys", "menu"), show="headings")
        tree.heading("command", text="Command")
        tree.heading("keys", text="Shortcut")
        tree.heading("menu", text="Menu")
        tree.column("command", width=300)
        tree.column("keys", width=180)
        tree.column("menu", width=100)
        sb = ttk.Scrollbar(win, command=tree.yview)
        tree.config(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        tree.pack(fill="both", expand=True, padx=(8, 0))
        extras = [("Column selection", "Alt + drag", "Mouse"),
                  ("Go to definition / open link or path", "Ctrl + click", "Mouse"),
                  ("Close tab", "Middle click / x on tab", "Mouse"),
                  ("Tab options (pin, color, copy path...)", "Right-click on tab", "Mouse"),
                  ("Toggle bookmark / fold", "Click line numbers / arrows", "Mouse"),
                  ("Zoom", "Ctrl + mouse wheel", "Mouse"),
                  ("Expand snippet / Emmet / next field", "Tab", "Editor"),
                  ("Show documentation tooltip", "Hover a name (Python)", "Mouse")]
        rows = []
        for cid in self.command_order:
            cmd = self.commands[cid]
            if cmd["kind"] == "radio":
                continue
            keys = ", ".join(seq_to_accel(k) for k in cmd["keys"]) or (cmd["accel"] or "")
            rows.append((cmd["label"], keys, cmd["menu"], cid))
        rows += [(a, b, c, None) for a, b, c in extras]

        def refresh(*_):
            tree.delete(*tree.get_children())
            words = query.get().lower().split()
            for label, keys, menu, cid in rows:
                hay = f"{label} {keys} {menu}".lower()
                if all(w in hay for w in words):
                    tree.insert("", "end", values=(label, keys, menu), tags=(cid or "",))

        def run(event=None):
            sel = tree.selection()
            if sel:
                cid = tree.item(sel[0], "tags")
                if cid and cid[0]:
                    win.destroy()
                    self.root.after(10, self.run_command, cid[0])

        query.trace_add("write", refresh)
        tree.bind("<Double-Button-1>", run)
        refresh()
        entry.focus_set()
        win.bind("<Escape>", lambda e: win.destroy())

    def about(self):
        mode = "portable" if os.path.normcase(CONFIG_DIR) == os.path.normcase(PORTABLE_DIR) \
            else "standard"
        messagebox.showinfo(
            f"About {APP}",
            f"{APP} {VERSION}\n\nA cross-platform text and code editor in a single Python file, "
            f"using only the standard library.\n\nPython {sys.version.split()[0]}\n"
            f"Tk {self.root.tk.call('info', 'patchlevel')}\n{sys.platform}\n\n"
            f"Settings ({mode} mode):\n{CONFIG_DIR}\n\nScript:\n"
            f"{SCRIPT_PATH or 'loaded with exec() (no file)'}")

    def open_settings_folder(self):
        os.makedirs(CONFIG_DIR, exist_ok=True)
        try:
            reveal_in_file_manager(CONFIG_DIR)
        except OSError as e:
            messagebox.showerror("Error", str(e))

    def open_error_log(self):
        if not os.path.exists(ERROR_LOG):
            messagebox.showinfo(APP, "No errors have been recorded.")
            return
        doc = self.open_file(ERROR_LOG)
        if doc:
            doc.text.see("end")

    def report_error(self, exc_type, exc_value, exc_tb):
        text = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
        try:
            os.makedirs(CONFIG_DIR, exist_ok=True)
            with open(ERROR_LOG, "a", encoding="utf-8") as f:
                f.write(f"--- {datetime.datetime.now().isoformat(timespec='seconds')} ---\n")
                f.write(text + "\n")
        except OSError:
            pass
        try:
            self.set_message(f"An unexpected error occurred: {exc_value}  (Help > Open Error Log)")
            self.root.bell()
        except tk.TclError:
            pass
        if not self._error_shown:
            self._error_shown = True
            try:
                messagebox.showerror(APP, f"An unexpected error occurred:\n\n{exc_value}\n\n"
                                          f"Details were saved to:\n{ERROR_LOG}")
            except tk.TclError:
                pass

    def reset_settings(self):
        if not messagebox.askyesno(APP, "Reset all settings to their defaults?\n\nYour files, "
                                        "snippets, themes and history are kept."):
            return
        for path in (CONFIG_FILE, KEYBINDINGS_FILE):
            try:
                os.remove(path)
            except OSError:
                pass
        self._reset_pending = True
        if messagebox.askyesno(APP, "Settings were reset. Restart Notepad now?"):
            cmd = self.relaunch_command("--new-window")
            if self.exit() and cmd:
                subprocess.Popen(cmd)

    def toggle_portable(self):
        if os.path.normcase(CONFIG_DIR) == os.path.normcase(PORTABLE_DIR):
            if messagebox.askyesno(APP, "Portable mode is ON: settings are stored next to the "
                                        f"script in\n{PORTABLE_DIR}\n\nTurn it off? Your "
                                        "settings will be copied to your user folder."):
                try:
                    shutil.copytree(PORTABLE_DIR, HOME_CONFIG_DIR, dirs_exist_ok=True)
                    os.rename(PORTABLE_DIR, PORTABLE_DIR + ".disabled-" +
                              time.strftime("%Y%m%d%H%M%S"))
                except OSError as e:
                    messagebox.showerror("Error", str(e))
                    return
                messagebox.showinfo(APP, "Portable mode turned off. Restart Notepad to apply.")
        else:
            if messagebox.askyesno(APP, "Portable mode stores all settings in a 'notepad_data' "
                                        "folder next to notepad.py, so you can carry it on a "
                                        "USB drive.\n\nTurn it on?"):
                try:
                    self.save_config()
                    shutil.copytree(CONFIG_DIR, PORTABLE_DIR, dirs_exist_ok=True) \
                        if os.path.isdir(CONFIG_DIR) else os.makedirs(PORTABLE_DIR)
                except OSError as e:
                    messagebox.showerror("Error", str(e))
                    return
                messagebox.showinfo(APP, "Portable mode turned on. Restart Notepad to apply.")

    def relaunch_command(self, *args):
        if SCRIPT_PATH:
            return [sys.executable, SCRIPT_PATH] + list(args)
        messagebox.showinfo(APP, "This option needs Notepad to be started from its .py file. "
                                 "It is not available when the code is run with exec().")
        return None

    def create_desktop_shortcut(self):
        if not self.relaunch_command():
            return
        home = os.path.expanduser("~")
        desktop = next((d for d in (os.path.join(home, "Desktop"),
                                    os.path.join(home, "OneDrive", "Desktop"),
                                    os.path.join(home, "Escritorio")) if os.path.isdir(d)), home)
        try:
            os.makedirs(CONFIG_DIR, exist_ok=True)
            icon_png = os.path.join(CONFIG_DIR, "icon.png")
            self.icon.write(icon_png, format="png")
            if sys.platform == "win32":
                python = sys.executable
                pythonw = os.path.join(os.path.dirname(python), "pythonw.exe")
                if os.path.exists(pythonw):
                    python = pythonw
                link = os.path.join(desktop, "Notepad.lnk")
                script = ("$s=(New-Object -COM WScript.Shell).CreateShortcut($env:NP_LINK);"
                          "$s.TargetPath=$env:NP_PY;$s.Arguments='\"'+$env:NP_SCRIPT+'\"';"
                          "$s.WorkingDirectory=$env:NP_DIR;$s.Save()")
                env = dict(os.environ, NP_LINK=link, NP_PY=python, NP_SCRIPT=SCRIPT_PATH,
                           NP_DIR=SCRIPT_DIR)
                subprocess.run(["powershell", "-NoProfile", "-Command", script], check=True,
                               env=env, creationflags=NO_WINDOW, timeout=30)
                target = link
            elif sys.platform == "darwin":
                target = os.path.join(desktop, "Notepad.command")
                with open(target, "w", encoding="utf-8") as f:
                    f.write(f'#!/bin/bash\nexec "{sys.executable}" "{SCRIPT_PATH}" "$@"\n')
                os.chmod(target, 0o755)
            else:
                entry = ("[Desktop Entry]\nType=Application\nName=Notepad\n"
                         "Comment=Text and code editor\n"
                         f'Exec="{sys.executable}" "{SCRIPT_PATH}" %F\nIcon={icon_png}\n'
                         "Terminal=false\nCategories=Utility;TextEditor;Development;\n"
                         "MimeType=text/plain;\n")
                apps = os.path.join(home, ".local", "share", "applications")
                os.makedirs(apps, exist_ok=True)
                target = os.path.join(apps, "pynotepad.desktop")
                for path in (target, os.path.join(desktop, "pynotepad.desktop")):
                    if os.path.isdir(os.path.dirname(path)):
                        with open(path, "w", encoding="utf-8") as f:
                            f.write(entry)
                        os.chmod(path, 0o755)
        except (OSError, subprocess.SubprocessError, tk.TclError) as e:
            messagebox.showerror("Error", f"Could not create the shortcut:\n{e}")
            return
        messagebox.showinfo(APP, f"Shortcut created:\n{target}")

    def run_self_test_process(self):
        cmd = self.relaunch_command("--selftest")
        if not cmd:
            return
        self._start_process(cmd, SCRIPT_DIR,
                            "Self-test")

    def doc_for(self, widget):
        return self.view_docs.get(str(widget))

    def _set_tag(self, widget, tag, enabled):
        tags = list(widget.bindtags())
        if enabled and tag not in tags:
            tags.insert(1 if tags and tags[0] == "NotepadMacro" else 0, tag)
        elif not enabled and tag in tags:
            tags.remove(tag)
        else:
            return
        widget.bindtags(tuple(tags))

    def column_start(self, event):
        w = event.widget
        doc = self.doc_for(w)
        if not doc or doc.kind != "text":
            return None
        index = w.index(f"@{event.x},{event.y}")
        line, col = map(int, index.split("."))
        doc.colsel = {"anchor": (line, col), "cur": (line, col), "view": w}
        self._set_tag(w, "NotepadColumn", True)
        w.tag_remove("sel", "1.0", "end")
        w.mark_set("insert", index)
        w.focus_set()
        self.column_draw(doc)
        return "break"

    def column_drag(self, event):
        w = event.widget
        doc = self.doc_for(w)
        if not doc or not doc.colsel:
            return None
        index = w.index(f"@{event.x},{event.y}")
        line = int(index.split(".")[0])
        x0 = w.bbox(f"{line}.0")
        cw = self.font.measure("0")
        if x0:
            col = max(0, round((event.x - x0[0]) / max(1, cw)))
        else:
            col = int(index.split(".")[1])
        doc.colsel["cur"] = (line, col)
        self.column_draw(doc)
        return "break"

    def column_rect(self, doc):
        (l1, c1), (l2, c2) = doc.colsel["anchor"], doc.colsel["cur"]
        return min(l1, l2), max(l1, l2), min(c1, c2), max(c1, c2)

    def column_draw(self, doc):
        t = doc.text
        t.tag_remove("colsel", "1.0", "end")
        if not doc.colsel:
            return
        top, bottom, left, right = self.column_rect(doc)
        for line in range(top, bottom + 1):
            length = len(doc._line(line))
            if left < length and right > left:
                t.tag_add("colsel", f"{line}.{left}", f"{line}.{min(right, length)}")
        lines = bottom - top + 1
        self.set_message(f"Column selection: {lines} lines x {right - left} columns  "
                         "(type to edit all lines, Esc to cancel)")

    def column_clear(self, doc):
        if doc.colsel:
            self._set_tag(doc.colsel["view"], "NotepadColumn", False)
        doc.colsel = None
        doc.text.tag_remove("colsel", "1.0", "end")

    def column_cancel_click(self, event):
        doc = self.doc_for(event.widget)
        if doc and doc.colsel and not (event.state & 0x8 or event.state & 0x20000):
            self.column_clear(doc)
        return None

    def column_text(self, doc):
        top, bottom, left, right = self.column_rect(doc)
        return "\n".join(doc._line(n)[left:right] for n in range(top, bottom + 1))

    def column_apply(self, doc, func):
        if not self._editable(doc):
            return
        top, bottom, left, right = self.column_rect(doc)
        lines = [doc._line(n) for n in range(top, bottom + 1)]
        new_lines = []
        new_col = left
        for i, line in enumerate(lines):
            if len(line) < left:
                line = line + " " * (left - len(line))
            new_line, new_col = func(line, left, right, i)
            new_lines.append(new_line)
        w = doc.colsel["view"]
        self.edit_block(doc, w, f"{top}.0", f"{bottom}.end", "\n".join(new_lines),
                        keep_cursor=False)
        doc.colsel["anchor"] = (top, new_col)
        doc.colsel["cur"] = (bottom, new_col)
        w.mark_set("insert", f"{bottom}.{new_col}")
        self.column_draw(doc)

    def column_key(self, event):
        w = event.widget
        doc = self.doc_for(w)
        if not doc or not doc.colsel:
            self._set_tag(w, "NotepadColumn", False)
            return None
        ctrl = bool(event.state & 0x4)
        key = event.keysym
        if key in ("Shift_L", "Shift_R", "Control_L", "Control_R", "Alt_L", "Alt_R"):
            return "break"
        if key == "Escape":
            self.column_clear(doc)
            return "break"
        if ctrl and key.lower() in ("c", "x"):
            self._copy(self.column_text(doc))
            if key.lower() == "x":
                self.column_apply(doc, lambda line, l, r, i: (line[:l] + line[r:], l))
            return "break"
        if ctrl and key.lower() == "v":
            try:
                clip = self.root.clipboard_get()
            except tk.TclError:
                return "break"
            parts = clip.split("\n")
            top, bottom, _, _ = self.column_rect(doc)
            count = bottom - top + 1

            def paste(line, l, r, i):
                piece = parts[i] if len(parts) == count else clip.replace("\n", " ")
                return line[:l] + piece + line[r:], l + len(piece)
            self.column_apply(doc, paste)
            return "break"
        if ctrl or event.state & 0x8 or event.state & 0x20000:
            self.column_clear(doc)
            return None
        if key == "BackSpace":
            def back(line, l, r, i):
                if r > l:
                    return line[:l] + line[r:], l
                return (line[:l - 1] + line[l:], l - 1) if l > 0 else (line, 0)
            self.column_apply(doc, back)
            return "break"
        if key == "Delete":
            self.column_apply(doc, lambda line, l, r, i: (line[:l] + line[max(r, l + 1):], l))
            return "break"
        if event.char and event.char.isprintable():
            ch = event.char
            self.column_apply(doc, lambda line, l, r, i: (line[:l] + ch + line[r:], l + 1))
            return "break"
        self.column_clear(doc)
        return None

    def toggle_vim(self):
        for doc in self.docs.values():
            doc.vim_mode = "normal"
            for w in doc.views():
                self.apply_vim_tags(doc, w)
        self.save_config()
        self.update_status()
        self.set_message("Vim mode on: Esc = normal mode, i = insert mode" if self.vim_var.get()
                         else "Vim mode off")

    def apply_vim_tags(self, doc, w):
        active = self.vim_var.get() and doc.kind == "text" and doc.vim_mode != "insert"
        self._set_tag(w, "NotepadVim", active)
        try:
            w.config(insertwidth=self.font.measure("0") if active else 2,
                     insertofftime=0 if active else 300)
        except tk.TclError:
            pass

    def vim_set_mode(self, doc, mode):
        doc.vim_mode = mode
        doc.vim_pending = ""
        for w in doc.views():
            self.apply_vim_tags(doc, w)
        if mode == "insert":
            doc.view().tag_remove("sel", "1.0", "end")
        self.update_status()

    def vim_key(self, event):
        w = event.widget
        doc = self.doc_for(w)
        if not doc or not self.vim_var.get() or doc.vim_mode == "insert":
            return None
        key = event.keysym
        if event.state & 0x4 or event.state & 0x8 or event.state & 0x20000:
            if event.state & 0x4 and key.lower() == "r" and not event.state & 0x1:
                w.event_generate("<<Redo>>")
                return "break"
            return None
        if key in ("Shift_L", "Shift_R", "Control_L", "Control_R", "Alt_L", "Alt_R",
                   "Caps_Lock"):
            return "break"
        if key in ("Up", "Down", "Left", "Right", "Prior", "Next", "Home", "End"):
            return None
        ch = event.char
        if key == "Escape":
            if doc.vim_mode in ("visual", "vline"):
                w.tag_remove("sel", "1.0", "end")
            self.vim_set_mode(doc, "normal")
            return "break"
        if not ch:
            return "break"
        pending = doc.vim_pending + ch
        m = re.fullmatch(r"(\d*)(.*)", pending)
        count = int(m.group(1)) if m.group(1) else 1
        cmd = m.group(2)
        if not cmd or (cmd.isdigit()):
            doc.vim_pending = pending if pending != "0" else ""
            if pending == "0":
                w.mark_set("insert", "insert linestart")
            return "break"
        if cmd in ("d", "y", "g", "c", ">", "<") and len(cmd) == 1:
            doc.vim_pending = pending
            return "break"
        doc.vim_pending = ""
        visual = doc.vim_mode in ("visual", "vline")
        anchor = getattr(doc, "vim_anchor", "insert")
        moves = {"h": "insert-1c", "l": "insert+1c", "j": "insert+1l", "k": "insert-1l",
                 "0": "insert linestart", "$": "insert lineend", "^": None,
                 "w": None, "b": None, "e": None, "G": None, "gg": "1.0"}
        if cmd in moves:
            for _ in range(count if cmd not in ("G", "gg", "0", "$", "^") else 1):
                if cmd == "w":
                    target = w.index("insert wordend")
                    m2 = re.search(r"\S", w.get(target, f"{target}+200c"))
                    target = f"{target}+{m2.start()}c" if m2 else target
                elif cmd == "b":
                    target = w.index("insert-1c wordstart")
                elif cmd == "e":
                    target = w.index("insert+1c wordend-1c")
                elif cmd == "G":
                    target = f"{count}.0" if m.group(1) else "end-1c linestart"
                elif cmd == "^":
                    line = w.get("insert linestart", "insert lineend")
                    target = f"insert linestart+{len(line) - len(line.lstrip())}c"
                else:
                    target = moves[cmd]
                if cmd == "l" and w.compare("insert", ">=", "insert lineend"):
                    break
                if cmd == "h" and w.compare("insert", "<=", "insert linestart"):
                    break
                w.mark_set("insert", target)
            w.see("insert")
            if visual:
                self._vim_visual_select(doc, w, anchor)
            return "break"
        if visual:
            if cmd in ("d", "x"):
                if w.tag_ranges("sel"):
                    self._copy(w.get("sel.first", "sel.last"))
                    w.delete("sel.first", "sel.last")
                self.vim_set_mode(doc, "normal")
            elif cmd == "y":
                if w.tag_ranges("sel"):
                    self._copy(w.get("sel.first", "sel.last"))
                w.tag_remove("sel", "1.0", "end")
                self.vim_set_mode(doc, "normal")
            elif cmd in (">", "<"):
                self.indent_lines(doc, w, dedent=cmd == "<")
                self.vim_set_mode(doc, "normal")
            elif cmd == "c":
                if w.tag_ranges("sel"):
                    w.delete("sel.first", "sel.last")
                self.vim_set_mode(doc, "insert")
            return "break"
        if cmd in ("i", "a", "A", "I", "o", "O"):
            if cmd == "a" and w.compare("insert", "<", "insert lineend"):
                w.mark_set("insert", "insert+1c")
            elif cmd == "A":
                w.mark_set("insert", "insert lineend")
            elif cmd == "I":
                line = w.get("insert linestart", "insert lineend")
                w.mark_set("insert", f"insert linestart+{len(line) - len(line.lstrip())}c")
            elif cmd in ("o", "O"):
                if not self._editable(doc):
                    return "break"
                indent = re.match(r"[ \t]*", w.get("insert linestart", "insert lineend")).group()
                if cmd == "o":
                    w.mark_set("insert", "insert lineend")
                    w.insert("insert", "\n" + indent)
                else:
                    w.mark_set("insert", "insert linestart")
                    w.insert("insert", indent + "\n")
                    w.mark_set("insert", "insert-1c")
            self.vim_set_mode(doc, "insert")
            return "break"
        if cmd in ("v", "V"):
            doc.vim_anchor = w.index("insert")
            doc.vim_mode = "visual" if cmd == "v" else "vline"
            self._vim_visual_select(doc, w, doc.vim_anchor)
            self.update_status()
            return "break"
        if not self._editable(doc) and cmd in ("x", "dd", "p", "P", "u", "D", "cc", "cw", "dw",
                                               ">>", "<<", "J", "r"):
            return "break"
        if cmd == "x":
            text = w.get("insert", f"insert+{count}c")
            if "\n" in text:
                text = text[:text.index("\n")]
            self._copy(text)
            w.delete("insert", f"insert+{len(text)}c")
        elif cmd in ("dd", "yy", "cc"):
            start = w.index("insert linestart")
            end = w.index(f"insert linestart+{count}l")
            text = w.get(start, end)
            if not text.endswith("\n"):
                text += "\n"
            self._copy(text)
            self.vim_register_line = True
            if cmd == "dd":
                if w.compare(end, ">=", "end-1c") and w.compare(start, ">", "1.0"):
                    w.delete(f"{start}-1c", "end-1c")
                else:
                    w.delete(start, end)
            elif cmd == "cc":
                w.delete(start, f"{end}-1c" if w.compare(end, "<", "end-1c") else "end-1c")
                self.vim_set_mode(doc, "insert")
        elif cmd in ("dw", "cw"):
            end = w.index("insert")
            for _ in range(count):
                end = w.index(f"{end} wordend")
            self._copy(w.get("insert", end))
            w.delete("insert", end)
            if cmd == "cw":
                self.vim_set_mode(doc, "insert")
        elif cmd == "D":
            self._copy(w.get("insert", "insert lineend"))
            w.delete("insert", "insert lineend")
        elif cmd in ("p", "P"):
            try:
                clip = self.root.clipboard_get()
            except tk.TclError:
                clip = ""
            if clip.endswith("\n"):
                if cmd == "p":
                    w.mark_set("insert", "insert lineend")
                    w.insert("insert", "\n" + clip[:-1] * 1)
                    w.mark_set("insert", "insert linestart")
                else:
                    w.mark_set("insert", "insert linestart")
                    w.insert("insert", clip)
                    w.mark_set("insert", "insert-1l linestart")
            else:
                if cmd == "p" and w.compare("insert", "<", "insert lineend"):
                    w.mark_set("insert", "insert+1c")
                w.insert("insert", clip * count)
        elif cmd == "u":
            for _ in range(count):
                try:
                    w.edit_undo()
                except tk.TclError:
                    break
        elif cmd in (">>", "<<"):
            self.indent_lines(doc, w, dedent=cmd == "<<")
        elif cmd == "J":
            self.join_lines()
        elif cmd == "/":
            self.show_find_bar()
        elif cmd == "n":
            self.find_next()
        elif cmd == "N":
            self.find_prev()
        elif cmd == ":":
            self.vim_command(doc)
        elif cmd == "gd":
            self.goto_definition()
        w.see("insert")
        return "break"

    def _vim_visual_select(self, doc, w, anchor):
        w.tag_remove("sel", "1.0", "end")
        a, b = sorted((w.index(anchor), w.index("insert")),
                      key=lambda i: tuple(map(int, i.split("."))))
        if doc.vim_mode == "vline":
            w.tag_add("sel", f"{a} linestart", f"{b} lineend+1c")
        else:
            w.tag_add("sel", a, f"{b}+1c")

    def vim_command(self, doc):
        command = simpledialog.askstring("Vim", ":", parent=self.root)
        if not command:
            return
        command = command.strip()
        if command.isdigit():
            self._goto(doc, int(command))
        elif command in ("w", "write"):
            self.save(doc)
        elif command in ("q", "quit"):
            self.close_tab(doc)
        elif command in ("q!",):
            doc.text.edit_modified(False)
            self.close_tab(doc, force=True)
        elif command in ("wq", "x"):
            if self.save(doc):
                self.close_tab(doc)
        elif command in ("qa", "qall"):
            self.exit()
        elif command.startswith(("s/", "%s/")):
            whole = command.startswith("%")
            parts = re.split(r"(?<!\\)/", command[2 if whole else 1:])
            if len(parts) >= 2:
                flags = parts[2] if len(parts) > 2 else ""
                try:
                    pattern = re.compile(parts[0], re.IGNORECASE if "i" in flags else 0)
                except re.error as e:
                    self.set_message(f"Invalid pattern: {e}")
                    return
                count = 0 if "g" in flags else 1
                w = doc.view()
                if whole:
                    new = "\n".join(pattern.sub(parts[1], l, count=count)
                                    for l in doc.content().split("\n"))
                    self.edit_block(doc, w, "1.0", "end-1c", new)
                else:
                    line = w.get("insert linestart", "insert lineend")
                    self.edit_block(doc, w, "insert linestart", "insert lineend",
                                    pattern.sub(parts[1], line, count=count))
        elif command in ("set nu", "set number"):
            self.line_numbers.set(True)
            self.toggle_line_numbers()
        elif command in ("set nonu", "set nonumber"):
            self.line_numbers.set(False)
            self.toggle_line_numbers()
        else:
            self.set_message(f"Unknown command: {command}")

    def _macro_capture(self, event):
        if not self.macro_recording or self._macro_playing:
            return None
        if event.keysym in ("F8", "Shift_L", "Shift_R", "Control_L", "Control_R", "Alt_L",
                            "Alt_R", "Caps_Lock", "Meta_L", "Meta_R", "Super_L", "Super_R"):
            return None
        self.macro.append((event.keysym, event.state & 0x2000D, event.char))
        return None

    def toggle_macro_recording(self):
        if self.macro_recording:
            self.macro_recording = False
            self.set_message(f"Macro recorded: {len(self.macro)} keys. Shift+F8 plays it.")
        else:
            self.macro = []
            self.macro_recording = True
            self.set_message("Recording macro... press F8 again to stop")
        self.update_status()

    def play_macro(self):
        doc, w = self.cv()
        if not doc:
            return
        if self.macro_recording:
            self.toggle_macro_recording()
        if not self.macro:
            self.set_message("No macro recorded (F8 starts recording)")
            return
        self._macro_playing = True
        try:
            w.focus_force()
            for keysym, state, char in self.macro:
                target = self.root.focus_get() or w
                if char and char.isprintable() and not state & 0x2000C and \
                        keysym not in OPEN_KEYS.values() and keysym not in CLOSE_KEYS.values() \
                        and keysym not in ("greater",):
                    target.insert("insert", char) if isinstance(target, tk.Text) else None
                else:
                    target.event_generate("<KeyPress>", keysym=keysym, state=state)
                self.root.update_idletasks()
        finally:
            self._macro_playing = False
        self.set_message(f"Macro played ({len(self.macro)} keys)")

    def after_copy(self):
        self.root.after_idle(self._record_clipboard)

    def before_paste(self, event=None):
        self._record_clipboard()
        doc = self.doc_for(event.widget) if event else None
        if doc and doc.kind == "text" and event is not None:
            w = event.widget
            if w.tag_ranges("sel") and not doc.read_only:
                try:
                    clip = self.root.clipboard_get()
                except tk.TclError:
                    return None
                first, last = w.index("sel.first"), w.index("sel.last")
                self.edit_block(doc, w, first, last, clip, keep_cursor=False)
                w.mark_set("insert", f"{first}+{len(clip)}c")
                w.see("insert")
                return "break"
        return None

    def _record_clipboard(self):
        try:
            text = self.root.clipboard_get()
        except tk.TclError:
            return
        if not text or len(text) > 1_000_000:
            return
        if text in self.clip_history:
            self.clip_history.remove(text)
        self.clip_history.insert(0, text)
        del self.clip_history[CLIP_HISTORY:]

    def paste_from_history(self):
        doc, w = self.cv()
        self._record_clipboard()
        if not doc or not self.clip_history:
            self.set_message("The clipboard history is empty")
            return
        if not self._editable(doc):
            return
        bbox = w.bbox("insert") or (10, 10, 0, 16)
        popup = tk.Toplevel(self.root)
        popup.overrideredirect(True)
        popup.geometry(f"+{w.winfo_rootx() + bbox[0]}+{w.winfo_rooty() + bbox[1] + bbox[3]}")
        th = self.theme
        lb = tk.Listbox(popup, height=min(12, len(self.clip_history)), width=60, font=self.font,
                        bg=th["bg"], fg=th["fg"], selectbackground=th["sel_bg"],
                        selectforeground=th["sel_fg"], activestyle="none", highlightthickness=1)
        lb.pack()
        for item in self.clip_history:
            one = item.replace("\n", "↵ ").replace("\t", " ")
            lb.insert("end", one[:80] + ("…" if len(one) > 80 else ""))
        lb.selection_set(0)
        lb.activate(0)

        def close(event=None):
            popup.destroy()
            w.focus_set()

        def choose(event=None):
            sel = lb.curselection()
            if sel:
                text = self.clip_history[sel[0]]
                if w.tag_ranges("sel"):
                    w.delete("sel.first", "sel.last")
                w.insert("insert", text)
                w.see("insert")
            close()
            return "break"

        lb.bind("<Return>", choose)
        lb.bind("<Double-Button-1>", choose)
        lb.bind("<Escape>", close)
        lb.bind("<FocusOut>", close)
        popup.after(10, lb.focus_set)

    def expand_selection(self):
        doc, w = self.cv()
        if not doc:
            return
        if w.tag_ranges("sel"):
            cur = (w.index("sel.first"), w.index("sel.last"))
        else:
            cur = (w.index("insert"), w.index("insert"))
            self._expand_stack = []
        candidates = []
        a, b = cur
        start = w.index(f"{a} wordstart")
        end = w.index(f"{b} wordend") if w.compare(b, ">", a) else w.index(f"{a} wordend")
        if re.fullmatch(r"\w+", w.get(start, end) or ""):
            candidates.append((start, end))
        content = doc.content()
        offset_a = self._offset(w, a)
        offset_b = self._offset(w, b)
        pairs = {"(": ")", "[": "]", "{": "}", '"': '"', "'": "'", "`": "`"}
        for opener, closer in pairs.items():
            depth = 0
            i = offset_a - 1
            found = None
            while i >= 0 and offset_a - i < 100_000:
                ch = content[i]
                if opener != closer and ch == closer:
                    depth += 1
                elif ch == opener:
                    if depth == 0:
                        found = i
                        break
                    depth -= 1
                if opener == closer and ch == "\n":
                    break
                i -= 1
            if found is None:
                continue
            depth = 0
            j = offset_b
            while j < len(content) and j - offset_b < 100_000:
                ch = content[j]
                if opener != closer and ch == opener:
                    depth += 1
                elif ch == closer:
                    if depth == 0:
                        candidates.append((f"1.0+{found + 1}c", f"1.0+{j}c"))
                        candidates.append((f"1.0+{found}c", f"1.0+{j + 1}c"))
                        break
                    depth -= 1
                if opener == closer and ch == "\n":
                    break
                j += 1
        candidates.append((w.index(f"{a} linestart"), w.index(f"{b} lineend")))
        first_line = int(w.index(a).split(".")[0])
        last_line = int(w.index(b).split(".")[0])
        block = doc._indent(doc._line(first_line))
        top, bottom = first_line, last_line
        while top > 1 and (not doc._line(top - 1).strip() or doc._indent(doc._line(top - 1)) >= block) \
                and block > 0:
            top -= 1
        while bottom < doc.last_line() and (not doc._line(bottom + 1).strip()
                                            or doc._indent(doc._line(bottom + 1)) >= block) \
                and block > 0:
            bottom += 1
        candidates.append((f"{top}.0", w.index(f"{bottom}.end")))
        candidates.append(("1.0", w.index("end-1c")))
        size = self._offset(w, b) - self._offset(w, a)
        best = None
        for s, e in candidates:
            s, e = w.index(s), w.index(e)
            if w.compare(s, "<=", a) and w.compare(e, ">=", b):
                length = self._offset(w, e) - self._offset(w, s)
                if length > size and (best is None or length < best[2]):
                    best = (s, e, length)
        if best:
            self._expand_stack.append(cur)
            w.tag_remove("sel", "1.0", "end")
            w.tag_add("sel", best[0], best[1])
            w.mark_set("insert", best[1])

    def shrink_selection(self):
        doc, w = self.cv()
        if not doc or not self._expand_stack:
            return
        a, b = self._expand_stack.pop()
        w.tag_remove("sel", "1.0", "end")
        if a != b:
            w.tag_add("sel", a, b)
        w.mark_set("insert", b)

    def word_at(self, w, index="insert"):
        line, col = map(int, w.index(index).split("."))
        text = w.get(f"{line}.0", f"{line}.end")
        for m in re.finditer(r"\w+", text):
            if m.start() <= col <= m.end():
                return m.group(), f"{line}.{m.start()}", f"{line}.{m.end()}"
        return None, None, None

    def rename_symbol(self):
        doc, w = self.cv()
        if not self._editable(doc):
            return
        if w.tag_ranges("sel"):
            old = w.get("sel.first", "sel.last")
        else:
            old = self.word_at(w)[0]
        if not old or not re.fullmatch(r"\w+", old):
            self.set_message("Place the cursor on a name to rename it")
            return
        new = simpledialog.askstring("Rename in File", f"Rename '{old}' to:", initialvalue=old,
                                     parent=self.root)
        if not new or new == old:
            return
        content = doc.content()
        skip = []
        if doc.lang:
            for m in LANGUAGES[doc.lang].finditer(content):
                if m.lastgroup.rsplit("_", 1)[0] in ("string", "comment"):
                    skip.append((m.start(), m.end()))
        starts = [s for s, _ in skip]
        count = 0
        out = []
        pos = 0
        for m in re.finditer(rf"\b{re.escape(old)}\b", content):
            k = bisect.bisect_right(starts, m.start()) - 1
            if k >= 0 and skip[k][0] <= m.start() < skip[k][1]:
                continue
            out.append(content[pos:m.start()])
            out.append(new)
            pos = m.end()
            count += 1
        out.append(content[pos:])
        if count:
            self.edit_block(doc, w, "1.0", "end-1c", "".join(out))
        self.set_message(f"Renamed {count} occurrence(s) of '{old}' (strings and comments were "
                         "left unchanged)")

    def step_number(self, delta):
        doc, w = self.cv()
        if not self._editable(doc):
            return
        line, col = map(int, w.index("insert").split("."))
        text = doc._line(line)
        for m in re.finditer(r"-?0[xX][0-9a-fA-F]+|-?\d+(?:\.\d+)?", text):
            if m.start() <= col <= m.end():
                s = m.group()
                if s.lower().lstrip("-").startswith("0x"):
                    value = int(s, 16) + delta
                    new = ("-" if value < 0 else "") + "0x" + format(abs(value), "X" if any(
                        c.isupper() for c in s[2:]) else "x").zfill(len(s.lstrip("-")) - 2)
                elif "." in s:
                    decimals = len(s.split(".")[1])
                    new = f"{float(s) + delta:.{decimals}f}"
                else:
                    new = str(int(s) + delta)
                self.edit_block(doc, w, f"{line}.{m.start()}", f"{line}.{m.end()}", new,
                                keep_cursor=False)
                w.mark_set("insert", f"{line}.{m.start() + len(new)}")
                return
        self.set_message("Place the cursor on a number")
        self.root.bell()

    def join_lines(self):
        doc, w = self.cv()
        if not self._editable(doc):
            return
        first, last = selected_lines(w)
        if first == last:
            if last >= doc.last_line():
                return
            last += 1
        lines = [doc._line(n) for n in range(first, last + 1)]
        joined = lines[0].rstrip() + "".join(" " + l.strip() for l in lines[1:] if l.strip())
        self.edit_block(doc, w, f"{first}.0", f"{last}.end", joined, keep_cursor=False)
        w.mark_set("insert", f"{first}.{len(lines[0].rstrip())}")

    def insert_snippet(self, doc, w, start, end, body):
        text = []
        stops = {}
        pos = 0
        for m in re.finditer(r"\$\{(\d+)(?::([^}]*))?\}|\$(\d+)", body):
            text.append(body[pos:m.start()])
            offset = sum(len(t) for t in text)
            number = int(m.group(1) or m.group(3))
            default = m.group(2) or ""
            text.append(default)
            stops.setdefault(number, []).append((offset, len(default)))
            pos = m.end()
        text.append(body[pos:])
        plain = "".join(text)
        start = w.index(start)
        self.edit_block(doc, w, start, end, plain, keep_cursor=False)
        order = sorted(n for n in stops if n > 0)
        marks = []
        for i, number in enumerate(order + ([0] if 0 in stops else [])):
            offset, length = stops[number][0]
            s_mark, e_mark = f"snip_{doc.id}_{i}_s", f"snip_{doc.id}_{i}_e"
            w.mark_set(s_mark, f"{start}+{offset}c")
            w.mark_gravity(s_mark, "left")
            w.mark_set(e_mark, f"{start}+{offset + length}c")
            w.mark_gravity(e_mark, "right")
            marks.append((s_mark, e_mark, number))
        if not marks:
            w.mark_set("insert", f"{start}+{len(plain)}c")
            doc.snippet = None
            return
        doc.snippet = {"marks": marks, "index": -1, "view": w}
        if not self.snippet_next(doc, w):
            w.mark_set("insert", f"{start}+{len(plain)}c")

    def snippet_next(self, doc, w):
        state = doc.snippet
        if not state or state["view"] is not w:
            doc.snippet = None
            return False
        state["index"] += 1
        if state["index"] >= len(state["marks"]):
            doc.snippet = None
            return False
        s_mark, e_mark, number = state["marks"][state["index"]]
        w.tag_remove("sel", "1.0", "end")
        if w.compare(s_mark, "<", e_mark):
            w.tag_add("sel", s_mark, e_mark)
        w.mark_set("insert", e_mark if number == 0 else s_mark)
        if w.compare(s_mark, "<", e_mark):
            w.mark_set("insert", e_mark)
        w.see("insert")
        if number == 0 or state["index"] == len(state["marks"]) - 1:
            doc.snippet = None
        return True

    def expand_emmet(self, doc, w):
        before = w.get("insert linestart", "insert")
        m = re.search(r"\S+$", before)
        if not m or "<" in m.group():
            return False
        abbr = m.group()
        result = emmet_expand(abbr, self.indent_unit(doc))
        if not result:
            return False
        text, cursor = result
        indent = re.match(r"[ \t]*", before).group()
        cursor += text[:cursor].count("\n") * len(indent)
        text = text.replace("\n", "\n" + indent)
        start = w.index(f"insert-{len(abbr)}c")
        self.edit_block(doc, w, start, "insert", text, keep_cursor=False)
        w.mark_set("insert", f"{start}+{cursor}c")
        w.see("insert")
        return True

    def toggle_fold(self):
        doc, w = self.cv()
        if doc and doc.kind == "text":
            line = int(w.index("insert").split(".")[0])
            if doc.toggle_fold(line) is None:
                self.set_message("Nothing to fold here")

    def fold_all(self):
        doc = self.current()
        if doc and doc.kind == "text":
            doc.fold_all()

    def unfold_all(self):
        doc = self.current()
        if doc:
            doc.unfold_all()

    def filter_view(self):
        doc = self.current()
        if not doc or doc.kind not in ("text", "large"):
            return
        term = simpledialog.askstring("Filter Lines View",
                                      "Show only lines matching (regular expression):",
                                      initialvalue=doc.filter_pattern or "", parent=self.root)
        if term is None:
            return
        if not term:
            self.clear_filter()
            return
        try:
            re.compile(term)
        except re.error as e:
            messagebox.showerror(APP, f"Invalid regular expression:\n{e}")
            return
        self.apply_filter(doc, term)

    def apply_filter(self, doc, term):
        pattern = re.compile(term, re.IGNORECASE)
        t = doc.text
        t.tag_remove("filtered_out", "1.0", "end")
        doc.filter_pattern = term
        lines = doc.content().split("\n")
        hidden = []
        for n, line in enumerate(lines, 1):
            if not pattern.search(line):
                hidden.extend((f"{n}.0", f"{n + 1}.0" if n < len(lines) else f"{n}.end"))
        for i in range(0, len(hidden), 2000):
            t.tag_add("filtered_out", *hidden[i:i + 2000])
        shown = len(lines) - len(hidden) // 2
        doc.redraw_gutter()
        self.set_message(f"Showing {shown:,} of {len(lines):,} lines matching '{term}' "
                         "(Search > Clear Line Filter to show all)")

    def clear_filter(self):
        doc = self.current()
        if doc:
            doc.text.tag_remove("filtered_out", "1.0", "end")
            doc.filter_pattern = None
            doc.redraw_gutter()
            self.set_message("Filter cleared")

    def goto_symbol(self):
        doc = self.current()
        if not doc or doc.kind != "text":
            return
        content = doc.content()
        symbols = find_symbols(content, doc.lang) if doc.lang else []
        if not symbols:
            self.set_message("No symbols found in this document")
            return
        win = tk.Toplevel(self.root)
        win.title("Go To Symbol")
        win.transient(self.root)
        x = self.root.winfo_rootx() + max(0, (self.root.winfo_width() - 520) // 2)
        win.geometry(f"520x360+{x}+{self.root.winfo_rooty() + 40}")
        query = tk.StringVar()
        entry = tk.Entry(win, textvariable=query, font=self.font)
        entry.pack(fill="x", padx=6, pady=6)
        lb = tk.Listbox(win, font=self.font, activestyle="none", exportselection=False)
        lb.pack(fill="both", expand=True, padx=6, pady=(0, 6))
        shown = []

        def refresh(*_):
            q = query.get().lower()
            shown[:] = [s for s in symbols if q in s["full"].lower()]
            lb.delete(0, "end")
            for s in shown:
                lb.insert("end", f"{'  ' * s['depth']}{s['name']}    :{s['line']}")
            if shown:
                lb.selection_set(0)

        def go(event=None):
            sel = lb.curselection() or ((0,) if shown else ())
            if sel:
                line = shown[sel[0]]["line"]
                win.destroy()
                self._goto(doc, line)
            return "break"

        def move(delta):
            sel = lb.curselection()
            if shown:
                i = max(0, min(len(shown) - 1, (sel[0] if sel else 0) + delta))
                lb.selection_clear(0, "end")
                lb.selection_set(i)
                lb.see(i)
            return "break"

        query.trace_add("write", refresh)
        entry.bind("<Return>", go)
        entry.bind("<Down>", lambda e: move(1))
        entry.bind("<Up>", lambda e: move(-1))
        lb.bind("<Double-Button-1>", go)
        win.bind("<Escape>", lambda e: win.destroy())
        refresh()
        entry.focus_set()

    def definition_patterns(self, name, lang):
        n = re.escape(name)
        if lang == "python":
            return [rf"^[ \t]*(?:async\s+)?(?:def|class)\s+{n}\b", rf"^{n}\s*(?::[^=\n]*)?=[^=]"]
        if lang in ("clike", "c"):
            return [rf"\b(?:function\*?|class|interface|struct|enum|type|func|fn|def)\s+{n}\b",
                    rf"\b(?:const|let|var)\s+{n}\b",
                    rf"^[ \t]*(?:[\w<>\[\],*&: ]+\s+)?{n}\s*\([^;{{]*\)\s*\{{"]
        if lang == "ruby":
            return [rf"^[ \t]*(?:def|class|module)\s+(?:self\.)?{n}\b"]
        if lang == "lua":
            return [rf"function\s+(?:[\w.:]+[.:])?{n}\b", rf"\blocal\s+{n}\b"]
        if lang in ("shell",):
            return [rf"^[ \t]*(?:function\s+)?{n}\s*\(\)"]
        if lang == "powershell":
            return [rf"(?i:function\s+{n}\b)"]
        if lang == "css":
            return [rf"--{n}\s*:", rf"\.{n}\b[^{{]*\{{"]
        if lang == "sql":
            return [rf"(?i:create\s+(?:table|view|function|procedure)\s+(?:if\s+not\s+exists\s+)?"
                    rf"{n}\b)"]
        if lang == "markdown":
            return [rf"^#+\s+.*{n}"]
        if lang == "batch":
            return [rf"^:{n}\b"]
        return [rf"\b(?:def|function|class|func|fn|sub)\s+{n}\b"]

    def goto_definition(self, name=None):
        doc, w = self.cv()
        if not doc or doc.kind != "text":
            return
        if not name:
            name = self.word_at(w)[0]
        if not name:
            self.set_message("Place the cursor on a name")
            return
        lang = doc.lang
        results = []
        searched = set()

        def search(text, owner, path):
            index = make_indexer(text)
            for pattern in self.definition_patterns(name, lang):
                for m in re.finditer(pattern, text, re.MULTILINE):
                    line = int(index(m.start()).split(".")[0])
                    results.append((owner, path, line, text.split("\n")[line - 1].strip()))
                if results:
                    return

        search(doc.content(), doc, doc.path)
        searched.add(doc.path)
        if not results:
            for other in self.ordered_docs():
                if other is not doc and other.kind == "text" and other.lang == lang:
                    search(other.content(), other, other.path)
                    searched.add(other.path)
        if not results and doc.path:
            ext = os.path.splitext(doc.path)[1]
            folder = os.path.dirname(doc.path)
            count = 0
            for dirpath, dirnames, filenames in os.walk(folder):
                dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
                for fname in filenames:
                    if not fname.endswith(ext):
                        continue
                    path = os.path.join(dirpath, fname)
                    if path in searched:
                        continue
                    count += 1
                    if count > 500:
                        break
                    try:
                        if os.path.getsize(path) > FIF_MAX_FILE:
                            continue
                        with open(path, "rb") as f:
                            text = decode_bytes(f.read())[0]
                    except OSError:
                        continue
                    search(text.replace("\r\n", "\n"), None, path)
                if count > 500:
                    break
        if not results:
            self.set_message(f"No definition found for '{name}'")
            self.root.bell()
            return
        if len(results) == 1:
            self._open_result(*results[0][:3])
            return
        win = tk.Toplevel(self.root)
        win.title(f"Definitions of {name}")
        win.transient(self.root)
        lb = tk.Listbox(win, width=90, height=min(12, len(results)), font=self.font)
        lb.pack(padx=6, pady=6, fill="both", expand=True)
        for owner, path, line, text in results:
            lb.insert("end", f"{os.path.basename(path or owner.name())}:{line}   {text[:80]}")

        def go(event=None):
            sel = lb.curselection()
            if sel:
                win.destroy()
                self._open_result(*results[sel[0]][:3])

        lb.bind("<Double-Button-1>", go)
        lb.bind("<Return>", go)
        win.bind("<Escape>", lambda e: win.destroy())
        lb.selection_set(0)
        lb.focus_set()

    def _open_result(self, owner, path, line):
        if owner is not None and str(owner.frame) in self.docs:
            self._goto(owner, line)
        elif path:
            doc = self.open_file(path)
            if doc:
                self._goto(doc, line)

    def on_ctrl_click(self, event):
        w = event.widget
        doc = self.doc_for(w)
        if not doc:
            return None
        index = w.index(f"@{event.x},{event.y}")
        line = w.get(f"{index} linestart", f"{index} lineend")
        col = int(index.split(".")[1])
        for m in re.finditer(r"https?://[^\s\"'<>)\]]+|(?:[A-Za-z]:)?[\w.~/\\-]+\.\w+(?::\d+)?",
                             line):
            if m.start() <= col <= m.end():
                if self.open_link(m.group(), doc):
                    return "break"
        w.mark_set("insert", index)
        name = self.word_at(w, index)[0]
        if name:
            self.goto_definition(name)
        return "break"

    def open_link(self, target, doc=None):
        if re.match(r"https?://", target):
            webbrowser.open(target)
            self.set_message(f"Opened {target}")
            return True
        base = os.path.dirname(doc.path) if doc and doc.path else os.getcwd()
        path, line, col = self.parse_file_arg(os.path.expanduser(target), base)
        if os.path.isfile(path):
            self.open_file(path, line=line, col=col)
            return True
        if target.startswith("#") and doc:
            slug = target[1:]
            for n, text in enumerate(doc.content().split("\n"), 1):
                m = re.match(r"#{1,6}\s+(.*?)\s*#*\s*$", text)
                if m and md_slug(m.group(1)) == slug:
                    self._goto(doc, n)
                    return True
        return False

    def lookup_doc(self, doc, expr):
        if doc.lang != "python" or not expr:
            return None
        parts = expr.split(".")
        name = parts[-1]
        try:
            for sym in python_symbols(doc.content()):
                if sym["name"] == name:
                    node = sym["node"]
                    sig = ""
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        sig = f"def {node.name}({ast.unparse(node.args)})"
                    else:
                        sig = f"class {node.name}"
                    return sig + "\n\n" + (ast.get_docstring(node) or "(no docstring)")
        except (SyntaxError, ValueError):
            pass
        obj = None
        if len(parts) == 1 and hasattr(builtins, name):
            obj = getattr(builtins, name)
        elif parts[0] in getattr(sys, "stdlib_module_names", set()) or parts[0] in sys.modules:
            try:
                obj = importlib.import_module(parts[0])
                for attr in parts[1:]:
                    obj = getattr(obj, attr)
            except (ImportError, AttributeError):
                obj = None
            except Exception:
                obj = None
        if obj is None:
            return None
        try:
            sig = f"{name}{inspect.signature(obj)}"
        except (TypeError, ValueError):
            sig = name
        return sig + "\n\n" + (inspect.getdoc(obj) or "(no documentation)")

    def _expr_at(self, w, index):
        line, col = map(int, w.index(index).split("."))
        text = w.get(f"{line}.0", f"{line}.end")
        for m in re.finditer(r"[A-Za-z_][\w.]*", text):
            if m.start() <= col < m.end():
                end = text.find(".", col)
                expr = m.group() if end < 0 or end >= m.end() else text[m.start():end]
                return expr.strip(".")
        return None

    def on_hover(self, event):
        if self._tip_job:
            self.root.after_cancel(self._tip_job)
            self._tip_job = None
        w = event.widget
        doc = self.doc_for(w)
        if not doc or doc.lang != "python":
            self.hide_tooltip()
            return
        index = w.index(f"@{event.x},{event.y}")
        expr = self._expr_at(w, index)
        if expr != self._tip_word:
            self.hide_tooltip()
        if expr and expr != self._tip_word:
            self._tip_job = self.root.after(
                700, lambda: self._show_tooltip(doc, expr, event.x_root, event.y_root))

    def _show_tooltip(self, doc, expr, x, y):
        self._tip_job = None
        text = self.lookup_doc(doc, expr)
        if not text:
            return
        self.hide_tooltip()
        lines = text.split("\n")
        if len(lines) > 18:
            lines = lines[:18] + ["...  (Shift+F1 shows everything)"]
        tip = tk.Toplevel(self.root)
        tip.overrideredirect(True)
        tip.geometry(f"+{x + 12}+{y + 16}")
        th = self.theme
        tk.Label(tip, text="\n".join(lines), justify="left", bg=th["gutter_bg"],
                 fg=th["fg"], font=self.font, padx=8, pady=6, bd=1, relief="solid",
                 wraplength=700).pack()
        self._tip = tip
        self._tip_word = expr

    def hide_tooltip(self, event=None):
        if self._tip is not None:
            try:
                self._tip.destroy()
            except tk.TclError:
                pass
        self._tip = None
        self._tip_word = None

    def show_documentation(self):
        doc, w = self.cv()
        if not doc:
            return
        expr = self._expr_at(w, "insert") or self._expr_at(w, "insert-1c")
        text = self.lookup_doc(doc, expr) if expr else None
        if not text and expr and doc.lang == "python":
            try:
                text = pydoc.render_doc(expr, renderer=pydoc.plaintext)
            except (ImportError, pydoc.ErrorDuringImport, AttributeError):
                text = None
            except Exception:
                text = None
        if not text:
            self.set_message("No documentation found (works for Python names)")
            self.root.bell()
            return
        self.open_virtual(f"Help: {expr}", text, "text", read_only=True)

    def insert_timestamp(self):
        doc, w = self.cv()
        if self._editable(doc):
            w.insert("insert", str(int(time.time())))

    def insert_uuid(self):
        doc, w = self.cv()
        if self._editable(doc):
            w.insert("insert", str(uuid.uuid4()))

    def special_characters(self):
        win = tk.Toplevel(self.root)
        win.title("Insert Special Character")
        win.transient(self.root)
        nb = ttk.Notebook(win)
        nb.pack(fill="both", expand=True, padx=6, pady=6)
        big = tkfont.Font(font=self.font)
        big.configure(size=self.font_size + 4)

        def insert(ch):
            doc, w = self.cv()
            if self._editable(doc):
                w.insert("insert", ch)

        for name, chars in SPECIAL_CHARS.items():
            frame = tk.Frame(nb)
            nb.add(frame, text=name)
            for i, ch in enumerate(chars.split()):
                tk.Button(frame, text=ch, width=3, font=big, command=lambda c=ch: insert(c)).grid(
                    row=i // 10, column=i % 10, padx=1, pady=1)
        search = tk.Frame(win)
        search.pack(fill="x", padx=6)
        tk.Label(search, text="Search by name or U+code:").pack(side="left")
        query = tk.StringVar()
        entry = tk.Entry(search, textvariable=query)
        entry.pack(side="left", fill="x", expand=True, padx=4)
        results = tk.Listbox(win, height=8, font=self.font)
        results.pack(fill="both", expand=True, padx=6, pady=6)
        found = []

        def do_search(event=None):
            q = query.get().strip()
            results.delete(0, "end")
            found.clear()
            m = re.fullmatch(r"(?:U\+|0x)?([0-9a-fA-F]{2,6})", q)
            if m and (q.lower().startswith(("u+", "0x")) or len(q) >= 4):
                try:
                    found.append(chr(int(m.group(1), 16)))
                except (ValueError, OverflowError):
                    pass
            if len(q) >= 3:
                words = q.upper().split()
                for code_point in range(0x20, 0x3000):
                    name = unicodedata.name(chr(code_point), "")
                    if name and all(word in name for word in words):
                        found.append(chr(code_point))
                        if len(found) >= 200:
                            break
            for ch in found:
                results.insert("end", f"{ch}    U+{ord(ch):04X}  {unicodedata.name(ch, '')}")

        def pick(event=None):
            sel = results.curselection()
            if sel:
                insert(found[sel[0]])

        entry.bind("<Return>", do_search)
        results.bind("<Double-Button-1>", pick)
        results.bind("<Return>", pick)
        win.bind("<Escape>", lambda e: win.destroy())

    def password_generator(self):
        win = tk.Toplevel(self.root)
        win.title("Generate Password")
        win.transient(self.root)
        win.resizable(False, False)
        length = tk.IntVar(value=20)
        opts = {name: tk.BooleanVar(value=True) for name in ("Uppercase", "Lowercase", "Digits",
                                                             "Symbols")}
        result = tk.StringVar()
        row = tk.Frame(win)
        row.pack(padx=10, pady=(10, 4), anchor="w")
        tk.Label(row, text="Length:").pack(side="left")
        tk.Spinbox(row, from_=6, to=128, width=5, textvariable=length).pack(side="left", padx=4)
        for name, var in opts.items():
            tk.Checkbutton(win, text=name, variable=var).pack(anchor="w", padx=10)
        entry = tk.Entry(win, textvariable=result, width=46, font=self.font)
        entry.pack(padx=10, pady=6)

        def generate():
            pools = {"Uppercase": string.ascii_uppercase, "Lowercase": string.ascii_lowercase,
                     "Digits": string.digits, "Symbols": "!@#$%^&*()-_=+[]{};:,.?/"}
            chosen = [pools[n] for n, v in opts.items() if v.get()] or [string.ascii_letters]
            try:
                n = max(len(chosen), min(128, int(length.get())))
            except (ValueError, tk.TclError):
                n = 20
            chars = [secrets.choice(pool) for pool in chosen]
            alphabet = "".join(chosen)
            chars += [secrets.choice(alphabet) for _ in range(n - len(chars))]
            secrets.SystemRandom().shuffle(chars)
            result.set("".join(chars))

        def do_insert():
            doc, w = self.cv()
            if self._editable(doc):
                w.insert("insert", result.get())
            win.destroy()

        buttons = tk.Frame(win)
        buttons.pack(pady=(0, 10))
        tk.Button(buttons, text="Generate", command=generate).pack(side="left", padx=3)
        tk.Button(buttons, text="Copy", command=lambda: self._copy(result.get())).pack(
            side="left", padx=3)
        tk.Button(buttons, text="Insert", command=do_insert).pack(side="left", padx=3)
        tk.Button(buttons, text="Close", command=win.destroy).pack(side="left", padx=3)
        generate()
        win.bind("<Escape>", lambda e: win.destroy())

    def pick_color(self):
        doc, w = self.cv()
        if not self._editable(doc):
            return
        line, col = map(int, w.index("insert").split("."))
        text = doc._line(line)
        found = None
        for m in re.finditer(r"#(?:[0-9a-fA-F]{6}|[0-9a-fA-F]{3})(?![0-9a-zA-Z_])", text):
            if m.start() <= col <= m.end():
                found = m
                break
        initial = found.group() if found else None
        if initial and len(initial) == 4:
            initial = "#" + "".join(c * 2 for c in initial[1:])
        _, color = colorchooser.askcolor(color=initial, parent=self.root, title="Pick Color")
        if not color:
            return
        color = color.upper()
        if found:
            self.edit_block(doc, w, f"{line}.{found.start()}", f"{line}.{found.end()}", color,
                            keep_cursor=False)
            w.mark_set("insert", f"{line}.{found.start() + len(color)}")
        elif w.tag_ranges("sel"):
            first = w.index("sel.first")
            self.edit_block(doc, w, first, "sel.last", color, keep_cursor=False)
        else:
            w.insert("insert", color)

    def insert_file(self):
        doc, w = self.cv()
        if not self._editable(doc):
            return
        path = filedialog.askopenfilename(title="Insert File")
        if not path:
            return
        result = self._read(path)
        if result:
            if result[3]:
                messagebox.showinfo(APP, "That file looks binary and was not inserted.")
                return
            w.insert("insert", result[0].replace("\r\n", "\n").replace("\r", "\n"))

    def test_data_dialog(self):
        win = tk.Toplevel(self.root)
        win.title("Generate Test Data")
        win.transient(self.root)
        win.resizable(False, False)
        rows = tk.IntVar(value=50)
        fmt = tk.StringVar(value="CSV")
        row = tk.Frame(win)
        row.pack(padx=10, pady=10)
        tk.Label(row, text="Rows:").pack(side="left")
        tk.Spinbox(row, from_=1, to=100000, width=7, textvariable=rows).pack(side="left", padx=4)
        for value in ("CSV", "JSON", "SQL"):
            tk.Radiobutton(row, text=value, value=value, variable=fmt).pack(side="left")

        def go():
            try:
                n = max(1, min(100000, int(rows.get())))
            except (ValueError, tk.TclError):
                n = 50
            win.destroy()
            ext = {"CSV": ".csv", "JSON": ".json", "SQL": ".sql"}[fmt.get()]
            self.open_virtual(f"test-data{ext}", generate_test_data(n, fmt.get()),
                              detect_language("x" + ext))
            doc = self.current()
            if doc:
                doc.display_name = None
                doc.default_ext = ext
                doc.lang_override = detect_language("x" + ext)
                doc.text.edit_modified(True)
                self.update_tab(doc)

        tk.Button(win, text="Generate", width=12, command=go).pack(pady=(0, 10))
        win.bind("<Escape>", lambda e: win.destroy())

    def convert_case_cmd(self, style):
        self._transform(lambda s: convert_case(s, style), "word")

    def reverse_lines(self):
        self._transform(lambda s: "\n".join(reversed(s.split("\n"))), "lines", "Lines reversed")

    def shuffle_lines(self):
        def shuffle(s):
            lines = s.split("\n")
            random.shuffle(lines)
            return "\n".join(lines)
        self._transform(shuffle, "lines", "Lines shuffled")

    def number_lines(self):
        def number(s):
            lines = s.split("\n")
            digits = len(str(len(lines)))
            return "\n".join(f"{i:>{digits}}. {line}" for i, line in enumerate(lines, 1))
        self._transform(number, "lines", "Lines numbered")

    def filter_lines(self, keep):
        term = simpledialog.askstring("Keep Lines" if keep else "Remove Lines",
                                      ("Keep" if keep else "Remove") +
                                      " lines matching (regular expression):", parent=self.root)
        if not term:
            return
        try:
            pattern = re.compile(term)
        except re.error as e:
            messagebox.showerror(APP, f"Invalid regular expression:\n{e}")
            return

        def apply(s):
            lines = s.split("\n")
            result = [l for l in lines if bool(pattern.search(l)) == keep]
            self.set_message(f"{len(lines) - len(result):,} line(s) removed")
            return "\n".join(result)
        self._transform(apply, "text")

    def align_columns(self):
        doc, w = self.cv()
        if not doc:
            return
        sample = w.get("sel.first", "sel.last") if w.tag_ranges("sel") else doc._line(
            int(w.index("insert").split(".")[0]))
        default = next((s for s in ("=", ":", ",", "|", "->", "=>") if s in sample), "=")
        sep = simpledialog.askstring("Align Columns", "Align on this text:", initialvalue=default,
                                     parent=self.root)
        if not sep:
            return

        def align(s):
            lines = s.split("\n")
            parts = [l.split(sep, 1) if sep in l else None for l in lines]
            width = max((len(p[0].rstrip()) for p in parts if p), default=0)
            out = []
            for line, p in zip(lines, parts):
                if p is None:
                    out.append(line)
                else:
                    pad = " " if sep not in (",", ":") else ""
                    out.append(p[0].rstrip().ljust(width) + pad + sep + " " + p[1].strip())
            return "\n".join(out)
        self._transform(align, "lines", "Columns aligned")

    def wrap_paragraph(self):
        doc, w = self.cv()
        if not self._editable(doc):
            return
        if w.tag_ranges("sel"):
            first, last = selected_lines(w)
        else:
            line = int(w.index("insert").split(".")[0])
            if not doc._line(line).strip():
                return
            first = last = line
            while first > 1 and doc._line(first - 1).strip():
                first -= 1
            while last < doc.last_line() and doc._line(last + 1).strip():
                last += 1
        lines = [doc._line(n) for n in range(first, last + 1)]
        m = re.match(r"^([ \t]*(?:#+|//|--|>|;|\*|-|\d+\.)?[ \t]*)", lines[0])
        prefix = m.group(1) if m else ""
        cont = re.sub(r"[-*]|\d+\.", lambda x: " " * len(x.group()), prefix)
        body = " ".join(l[len(prefix):].strip() if l.startswith(prefix.rstrip()) else l.strip()
                        for l in lines)
        width = max(20, self.ruler_col.get())
        wrapped = textwrap.fill(body, width=width, initial_indent=prefix,
                                subsequent_indent=cont if prefix.strip() in ("-", "*") or
                                re.fullmatch(r"\s*\d+\.\s*", prefix) else prefix)
        self.edit_block(doc, w, f"{first}.0", f"{last}.end", wrapped)
        self.set_message(f"Paragraph wrapped at {width} columns")

    def clean_invisible_cmd(self):
        self._transform(clean_invisible, "text", "Invisible characters removed")

    def straighten_quotes_cmd(self):
        self._transform(straighten_quotes, "text", "Quotes straightened")

    def normalize_unicode(self):
        self._transform(lambda s: unicodedata.normalize("NFC", s), "text", "Unicode normalized")

    def escape_tool(self, kind):
        def json_unescape(s):
            try:
                return json.loads('"' + s + '"')
            except ValueError as e:
                raise ToolError(f"Not a valid JSON string: {e}")
        funcs = {"html_e": lambda s: html.escape(s), "html_d": html.unescape,
                 "json_e": lambda s: json.dumps(s, ensure_ascii=False)[1:-1],
                 "json_d": json_unescape, "regex": re.escape}
        self._transform(funcs[kind], "text")

    def sort_json_keys(self):
        doc = self.current()

        def sort(s):
            try:
                data = json.loads(s)
            except json.JSONDecodeError as e:
                raise ToolError(f"Invalid JSON: {e.msg} (line {e.lineno}, column {e.colno})",
                                e.lineno)
            indent = doc.indent_width if doc and doc.indent_spaces else "\t"
            return json.dumps(data, ensure_ascii=False, indent=indent, sort_keys=True)
        self._transform(sort, "text", "JSON keys sorted")

    def check_syntax(self, doc, quiet=False):
        t = doc.text
        t.tag_remove("syntax_error", "1.0", "end")
        doc.syntax_error = None
        content = doc.content()
        ext = os.path.splitext(doc.path or doc.display_name or "")[1].lower()
        error = None
        checked = True
        try:
            if doc.lang == "python":
                compile(content, doc.path or "<editor>", "exec")
            elif doc.lang == "json" and content.strip():
                json.loads(content)
            elif doc.lang == "ini" and ext == ".toml" and tomllib:
                tomllib.loads(content)
            elif doc.lang == "markup" and ext in (".xml", ".svg", ".xaml", ".csproj", ".config",
                                                  ".plist", ".xsl", ".xslt") and content.strip():
                xml.dom.minidom.parseString(content.encode("utf-8"))
            else:
                checked = False
        except SyntaxError as e:
            error = (e.lineno or 1, e.msg)
        except json.JSONDecodeError as e:
            error = (e.lineno, e.msg)
        except ExpatError as e:
            error = (e.lineno, str(e))
        except ValueError as e:
            m = re.search(r"line (\d+)", str(e))
            error = (int(m.group(1)) if m else 1, str(e))
        if error:
            line = max(1, min(error[0], doc.last_line()))
            doc.syntax_error = (line, error[1])
            t.tag_add("syntax_error", f"{line}.0", f"{line}.end")
            self.set_message(f"Syntax error on line {line}: {error[1]}")
            if not quiet:
                self._goto(doc, line)
                self.root.bell()
        elif checked and not quiet:
            self.set_message("No syntax errors found")
        elif not checked and not quiet:
            self.set_message("Validation is available for Python, JSON, TOML and XML")
        doc.redraw_gutter()
        return error

    def validate_cmd(self):
        doc = self.current()
        if doc and doc.kind == "text":
            self.check_syntax(doc)

    def json_tree(self):
        doc = self.current()
        if not doc:
            return
        try:
            data = json.loads(doc.content())
        except json.JSONDecodeError as e:
            messagebox.showerror(APP, f"Invalid JSON: {e.msg} (line {e.lineno}, column {e.colno})")
            return
        win = tk.Toplevel(self.root)
        win.title(f"JSON Tree - {doc.name()}")
        win.geometry("760x520")
        tree = ttk.Treeview(win, columns=("value", "type"))
        tree.heading("#0", text="Key")
        tree.heading("value", text="Value")
        tree.heading("type", text="Type")
        tree.column("#0", width=260)
        tree.column("value", width=380)
        tree.column("type", width=80)
        sb = ttk.Scrollbar(win, command=tree.yview)
        tree.config(yscrollcommand=sb.set)
        path_var = tk.StringVar(value="$")
        bottom = tk.Frame(win)
        bottom.pack(side="bottom", fill="x")
        tk.Entry(bottom, textvariable=path_var, state="readonly").pack(side="left", fill="x",
                                                                      expand=True, padx=4,
                                                                      pady=4)
        tk.Button(bottom, text="Copy Path", command=lambda: self._copy(path_var.get())).pack(
            side="right", padx=4)
        sb.pack(side="right", fill="y")
        tree.pack(fill="both", expand=True)
        paths = {}
        count = [0]

        def add(parent, key, value, path):
            count[0] += 1
            if count[0] > 20000:
                return
            kind = type(value).__name__
            if isinstance(value, dict):
                node = tree.insert(parent, "end", text=str(key), values=(f"{{{len(value)}}}", kind),
                                   open=count[0] < 50)
                for k, v in value.items():
                    sub = f"{path}.{k}" if re.fullmatch(r"[A-Za-z_]\w*", k) else \
                        f"{path}[{json.dumps(k)}]"
                    add(node, k, v, sub)
            elif isinstance(value, list):
                node = tree.insert(parent, "end", text=str(key), values=(f"[{len(value)}]", kind),
                                   open=count[0] < 50)
                for i, v in enumerate(value):
                    add(node, f"[{i}]", v, f"{path}[{i}]")
            else:
                node = tree.insert(parent, "end", text=str(key),
                                   values=(json.dumps(value, ensure_ascii=False)[:500],
                                           "null" if value is None else kind))
            paths[node] = path

        add("", "$", data, "$")

        def select(event=None):
            sel = tree.selection()
            if sel:
                path_var.set(paths.get(sel[0], "$"))

        tree.bind("<<TreeviewSelect>>", select)
        win.bind("<Escape>", lambda e: win.destroy())

    def csv_table(self):
        doc = self.current()
        if not doc:
            return
        content = doc.content()
        if not content.strip():
            return
        sample = content[:20000]
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
            header = csv.Sniffer().has_header(sample)
        except csv.Error:
            dialect, header = csv.excel, True
        rows = list(csv.reader(io.StringIO(content), dialect))
        rows = [r for r in rows if r]
        if not rows:
            return
        width = max(len(r) for r in rows)
        names = rows[0] if header else [f"Column {i + 1}" for i in range(width)]
        names = [n or f"Column {i + 1}" for i, n in enumerate(names + [""] * (width - len(names)))]
        data = rows[1:] if header else rows
        win = tk.Toplevel(self.root)
        win.title(f"CSV Table - {doc.name()}  ({len(data):,} rows)")
        win.geometry("900x520")
        cols = [f"c{i}" for i in range(width)]
        frame = tk.Frame(win)
        frame.pack(fill="both", expand=True)
        tree = ttk.Treeview(frame, columns=cols, show="headings")
        ys = ttk.Scrollbar(frame, command=tree.yview)
        xs = ttk.Scrollbar(frame, orient="horizontal", command=tree.xview)
        tree.config(yscrollcommand=ys.set, xscrollcommand=xs.set)
        ys.pack(side="right", fill="y")
        xs.pack(side="bottom", fill="x")
        tree.pack(fill="both", expand=True)
        order = {"col": None, "rev": False}

        def fill():
            tree.delete(*tree.get_children())
            for r in data[:50000]:
                tree.insert("", "end", values=r + [""] * (width - len(r)))

        def sort_by(i):
            order["rev"] = not order["rev"] if order["col"] == i else False
            order["col"] = i

            def key(r):
                v = r[i] if i < len(r) else ""
                try:
                    return (0, float(v.replace(",", "")), "")
                except ValueError:
                    return (1, 0, v.lower())
            data.sort(key=key, reverse=order["rev"])
            fill()

        for i, (c, n) in enumerate(zip(cols, names)):
            tree.heading(c, text=n, command=lambda i=i: sort_by(i))
            tree.column(c, width=max(80, min(260, self.font.measure(n) + 30)), stretch=False)
        fill()
        tk.Label(win, text="Click a column header to sort. The document is not modified.",
                 anchor="w").pack(fill="x", padx=6)
        win.bind("<Escape>", lambda e: win.destroy())

    def convert_number(self, base):
        def conv(s):
            text = s.strip()
            try:
                value = int(text.replace("_", ""), 0)
            except ValueError:
                try:
                    value = int(text, 16) if re.fullmatch(r"[0-9a-fA-F]+", text) else None
                except ValueError:
                    value = None
            if value is None:
                raise ToolError("Select a number (decimal, 0x hex, 0b binary or 0o octal).")
            return {"dec": str(value), "hex": hex(value), "bin": bin(value),
                    "oct": oct(value)}[base]
        self._transform(conv, "word")

    def convert_timestamp(self):
        def conv(s):
            text = s.strip()
            if re.fullmatch(r"-?\d{9,13}(?:\.\d+)?", text):
                value = float(text)
                if abs(value) > 1e11:
                    value /= 1000
                return datetime.datetime.fromtimestamp(value).strftime("%Y-%m-%d %H:%M:%S")
            try:
                moment = datetime.datetime.fromisoformat(text.replace("Z", "+00:00"))
            except ValueError:
                raise ToolError("Select a Unix timestamp or a date like 2026-11-06 14:30:00.")
            return str(int(moment.timestamp()))
        doc, w = self.cv()
        if doc and not w.tag_ranges("sel"):
            line = w.get("insert linestart", "insert lineend")
            col = int(w.index("insert").split(".")[1])
            for m in re.finditer(r"-?\d{9,13}(?:\.\d+)?|\d{4}-\d{2}-\d{2}(?:[T ]\d{2}:\d{2}"
                                 r"(?::\d{2}(?:\.\d+)?)?(?:Z|[+-]\d{2}:\d{2})?)?", line):
                if m.start() <= col <= m.end():
                    row = w.index("insert").split(".")[0]
                    w.tag_add("sel", f"{row}.{m.start()}", f"{row}.{m.end()}")
                    break
        self._transform(conv, "word")

    def text_statistics(self):
        doc, w = self.cv()
        if not doc:
            return
        text = w.get("sel.first", "sel.last") if w.tag_ranges("sel") else doc.content()
        words = re.findall(r"\w+(?:['’-]\w+)*", text)
        sentences = len([s for s in re.split(r"[.!?]+(?:\s|$)", text) if s.strip()])
        paragraphs = len([p for p in re.split(r"\n\s*\n", text) if p.strip()])
        freq = {}
        for word in words:
            lw = word.lower()
            if len(lw) > 3:
                freq[lw] = freq.get(lw, 0) + 1
        top = sorted(freq.items(), key=lambda x: (-x[1], x[0]))[:10]
        minutes = len(words) / 200
        scope = "Selection" if w.tag_ranges("sel") else "Document"
        no_spaces = len(re.sub(r"\s", "", text))
        lines = text.count("\n") + 1
        messagebox.showinfo(
            "Text Statistics",
            f"{scope}\n\n"
            f"Characters: {len(text):,}\nCharacters (no spaces): {no_spaces:,}\n"
            f"Words: {len(words):,}\nLines: {lines:,}\n"
            f"Sentences: {sentences:,}\nParagraphs: {paragraphs:,}\n"
            f"Reading time: {int(minutes)} min {int(minutes % 1 * 60)} s\n\n"
            "Most used words:\n" + "\n".join(f"  {w_}: {n}" for w_, n in top))

    def set_word_goal(self):
        doc = self.current()
        if not doc:
            return
        goal = simpledialog.askinteger("Word Goal", "Word goal for this document (0 to remove):",
                                       initialvalue=doc.word_goal or 500, minvalue=0,
                                       parent=self.root)
        if goal is not None:
            doc.word_goal = goal
            self.update_status()

    def toggle_pomodoro(self):
        if self.pomodoro:
            if self.pomodoro.get("job"):
                self.root.after_cancel(self.pomodoro["job"])
            self.pomodoro = None
            self.status_items["pomodoro"].config(text="")
            self.layout_status()
            self.set_message("Pomodoro stopped")
            return
        self.pomodoro = {"phase": "Focus", "end": time.time() + 25 * 60, "job": None, "count": 0}
        self.set_message("Pomodoro started: 25 minutes of focus")
        self._pomodoro_tick()

    def _pomodoro_tick(self):
        p = self.pomodoro
        if not p:
            return
        left = int(p["end"] - time.time())
        if left <= 0:
            self.root.bell()
            if p["phase"] == "Focus":
                p["count"] += 1
                long_break = p["count"] % 4 == 0
                p["phase"] = "Break"
                p["end"] = time.time() + (15 if long_break else 5) * 60
                message = f"Time for a {'long ' if long_break else ''}break!"
            else:
                p["phase"] = "Focus"
                p["end"] = time.time() + 25 * 60
                message = "Break is over. Back to focus!"
            self.set_message(message)
            self.root.after(10, lambda: messagebox.showinfo("Pomodoro", message))
            left = int(p["end"] - time.time())
        self.status_items["pomodoro"].config(text=f"{p['phase']} {left // 60:02d}:{left % 60:02d}")
        self.layout_status()
        p["job"] = self.root.after(1000, self._pomodoro_tick)

    def regex_tester(self):
        doc, w = self.cv()
        win = tk.Toplevel(self.root)
        win.title("Regex Tester")
        win.geometry("760x560")
        top = tk.Frame(win)
        top.pack(fill="x", padx=6, pady=6)
        tk.Label(top, text="Pattern:").pack(side="left")
        pattern_var = tk.StringVar(value=self.find_var.get() if self.opt_regex.get() else "")
        entry = tk.Entry(top, textvariable=pattern_var, font=self.font)
        entry.pack(side="left", fill="x", expand=True, padx=4)
        flags = {name: tk.BooleanVar(value=False) for name in ("IGNORECASE", "MULTILINE",
                                                               "DOTALL", "VERBOSE")}
        frow = tk.Frame(win)
        frow.pack(fill="x", padx=6)
        for name, var in flags.items():
            tk.Checkbutton(frow, text=name.capitalize(), variable=var).pack(side="left")
        tk.Label(win, text="Test text:", anchor="w").pack(fill="x", padx=6)
        sample = tk.Text(win, height=10, font=self.font, undo=True, wrap="none")
        sample.pack(fill="both", expand=True, padx=6)
        if doc:
            text = w.get("sel.first", "sel.last") if w.tag_ranges("sel") else doc.content()[:20000]
            sample.insert("1.0", text)
        sample.tag_configure("m0", background="#FFE58A", foreground="#000000")
        sample.tag_configure("m1", background="#A8E6A1", foreground="#000000")
        status = tk.Label(win, anchor="w")
        status.pack(fill="x", padx=6)
        results = tk.Listbox(win, height=8, font=self.font)
        results.pack(fill="both", expand=True, padx=6, pady=(0, 6))
        job = [None]

        def run():
            job[0] = None
            sample.tag_remove("m0", "1.0", "end")
            sample.tag_remove("m1", "1.0", "end")
            results.delete(0, "end")
            pat = pattern_var.get()
            if not pat:
                status.config(text="Type a pattern")
                return
            flag = 0
            for name, var in flags.items():
                if var.get():
                    flag |= getattr(re, name)
            try:
                regex = re.compile(pat, flag)
            except re.error as e:
                status.config(text=f"Error: {e}")
                return
            text = sample.get("1.0", "end-1c")
            index = make_indexer(text)
            count = 0
            for i, m in enumerate(regex.finditer(text)):
                if m.end() == m.start():
                    continue
                count += 1
                if count > 2000:
                    break
                sample.tag_add(f"m{i % 2}", index(m.start()), index(m.end()))
                groups = "  ".join(f"[{k}] {g!r}" for k, g in enumerate(m.groups(), 1))
                named = "  ".join(f"<{k}> {v!r}" for k, v in m.groupdict().items())
                results.insert("end", f"{index(m.start())}  {m.group()!r}  {groups}  {named}")
            status.config(text=f"{count:,} match(es)")

        def schedule(*_):
            if job[0]:
                win.after_cancel(job[0])
            job[0] = win.after(200, run)

        pattern_var.trace_add("write", schedule)
        for var in flags.values():
            var.trace_add("write", schedule)
        sample.bind("<<Modified>>", lambda e: (schedule(), sample.edit_modified(False)))

        def use():
            self.find_var.set(pattern_var.get())
            self.opt_regex.set(True)
            self.show_find_bar()

        tk.Button(win, text="Use in Find Bar", command=use).pack(side="right", padx=6, pady=(0, 6))
        entry.focus_set()
        schedule()
        win.bind("<Escape>", lambda e: win.destroy())

    def md_wrap(self, marker):
        doc, w = self.cv()
        if not doc or doc.lang != "markdown":
            self.set_message("This shortcut works in Markdown documents")
            return
        if not self._editable(doc):
            return
        if w.tag_ranges("sel"):
            first, last = w.index("sel.first"), w.index("sel.last")
            inner = w.get(first, last)
            if inner.startswith(marker) and inner.endswith(marker) and len(inner) >= 2 * len(marker):
                new = inner[len(marker):-len(marker)]
            else:
                new = marker + inner + marker
            self.edit_block(doc, w, first, last, new, select=True)
        else:
            w.insert("insert", marker + marker)
            w.mark_set("insert", f"insert-{len(marker)}c")

    def insert_toc(self):
        doc, w = self.cv()
        if not self._editable(doc):
            return
        toc = markdown_toc(doc.content())
        if not toc:
            self.set_message("No headings found")
            return
        w.insert("insert", toc + "\n")

    def _start_process(self, cmd, cwd, title, env_extra=None):
        if self.proc and self.proc.poll() is None:
            if not messagebox.askyesno(APP, "A program is still running. Stop it and run this "
                                            "one?"):
                return False
            self.stop_run()
        self.show_output()
        self.clear_output()
        self._run_cwd = cwd
        self._out_append("$ " + " ".join(shlex.quote(c) for c in cmd) + "\n", "info")
        env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUNBUFFERED="1")
        if env_extra:
            env.update(env_extra)
        try:
            self.proc = subprocess.Popen(
                cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                stdin=subprocess.DEVNULL, env=env, creationflags=NO_WINDOW)
        except OSError as e:
            self._out_append(f"Could not start the program:\n{e}\n", "error")
            self.proc = None
            return False
        self._run_started = time.monotonic()
        self._out_queue = queue.Queue()
        self._out_decoder = codecs.getincrementaldecoder("utf-8")(errors="replace")
        threading.Thread(target=self._read_output, args=(self.proc, self._out_queue),
                         daemon=True).start()
        self.set_message(f"Running {title}...")
        self.root.after(50, self._poll_output)
        return True

    def _python_cmd(self):
        python = sys.executable
        if os.path.basename(python).lower() == "pythonw.exe":
            console = os.path.join(os.path.dirname(python), "python.exe")
            if os.path.exists(console):
                python = console
        return python

    def run_selection(self):
        doc, w = self.cv()
        if not doc:
            return
        if not w.tag_ranges("sel"):
            self.set_message("Select some code first")
            return
        code_text = textwrap.dedent(w.get("sel.first", "sel.last"))
        ext = RUN_SELECTION_EXT.get(doc.lang)
        if not ext:
            messagebox.showinfo(APP, "Run Selection supports Python, shell, PowerShell, "
                                     "JavaScript, Ruby, Lua and batch files.")
            return
        fd, tmp = tempfile.mkstemp(prefix="notepad_sel_", suffix=ext)
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as f:
            f.write(code_text if ext != ".bat" else code_text.replace("\n", "\r\n"))
        cmd = self._runner(tmp)
        if not cmd:
            messagebox.showinfo(APP, "No program was found to run this code.")
            return
        cwd = os.path.dirname(doc.path) if doc.path else os.getcwd()
        self._start_process(cmd, cwd, "selection")

    def project_root(self, doc):
        folder = os.path.dirname(doc.path) if doc and doc.path else os.getcwd()
        out = git_run(["rev-parse", "--show-toplevel"], folder)
        if out:
            return out.decode("utf-8", errors="replace").strip()
        return folder

    def run_tests(self):
        doc = self.current()
        if doc and doc.modified() and doc.path:
            self.save(doc)
        root = self.project_root(doc)
        python = self._python_cmd()
        if importlib.util.find_spec("pytest"):
            cmd = [python, "-m", "pytest", "-q"]
        else:
            cmd = [python, "-m", "unittest", "discover", "-v"]
        self._start_process(cmd, root, "tests")

    def run_profiler(self):
        doc = self.current()
        if not doc or doc.lang != "python":
            messagebox.showinfo(APP, "The profiler works with Python files.")
            return
        if (not doc.path or doc.modified()) and not self.save(doc):
            return
        self._start_process([self._python_cmd(), "-m", "cProfile", "-s", "cumulative", doc.path],
                            os.path.dirname(doc.path), f"{doc.name()} (profiler)")

    def send_http_request(self):
        doc, w = self.cv()
        if not doc:
            return
        lines, blocks, variables = parse_http_blocks(doc.content())
        line = int(w.index("insert").split(".")[0]) - 1
        block = next(((s, e) for s, e in blocks if s <= line <= e), blocks[0] if blocks else None)
        request = parse_http_request(lines[block[0]:block[1] + 1], variables) if block else None
        if not request:
            messagebox.showinfo(APP, "Put the cursor inside a request such as:\n\n"
                                     "GET https://example.com/api\nAccept: application/json\n\n"
                                     "Separate requests with a line starting with ###.")
            return
        method, url, headers, body = request
        self.show_output()
        self.clear_output()
        self._out_append(f"{method} {url}\n", "info")
        self.set_message(f"Sending {method} {url}...")
        result = queue.Queue()

        def worker():
            started = time.monotonic()
            req = urllib.request.Request(url, data=body.encode("utf-8") if body else None,
                                         headers=headers, method=method)
            try:
                with urllib.request.urlopen(req, timeout=30) as resp:
                    data = resp.read(10 * 1024 * 1024)
                    result.put((resp.status, resp.reason, dict(resp.headers), data,
                                time.monotonic() - started, None))
            except urllib.error.HTTPError as e:
                data = e.read(10 * 1024 * 1024) if e.fp else b""
                result.put((e.code, e.reason, dict(e.headers or {}), data,
                            time.monotonic() - started, None))
            except (urllib.error.URLError, OSError, ValueError) as e:
                result.put((None, None, {}, b"", time.monotonic() - started, str(e)))

        threading.Thread(target=worker, daemon=True).start()

        def poll():
            try:
                status, reason, resp_headers, data, secs, error = result.get_nowait()
            except queue.Empty:
                self.root.after(100, poll)
                return
            if error:
                self._out_append(f"Request failed: {error}\n", "error")
                self.set_message("Request failed")
                return
            ctype = next((v for k, v in resp_headers.items() if k.lower() == "content-type"), "")
            charset = re.search(r"charset=([\w-]+)", ctype)
            text = data.decode(charset.group(1) if charset else "utf-8", errors="replace")
            lang = None
            if "json" in ctype:
                try:
                    text = json.dumps(json.loads(text), indent=4, ensure_ascii=False)
                    lang = "json"
                except ValueError:
                    pass
            elif "html" in ctype or "xml" in ctype:
                lang = "markup"
            head = "\n".join(f"{k}: {v}" for k, v in resp_headers.items())
            self._out_append(f"HTTP {status} {reason}   ({secs * 1000:.0f} ms, "
                             f"{format_bytes(len(data))})\n{head}\n",
                             "info" if status and status < 400 else "error")
            self.open_virtual(f"Response {status} - {method} {urllib.parse.urlparse(url).path or '/'}",
                              text, lang, read_only=True)
            self.set_message(f"HTTP {status} {reason} in {secs * 1000:.0f} ms")

        self.root.after(100, poll)

    def run_sql(self):
        doc, w = self.cv()
        if not doc or doc.kind != "text":
            return
        if not doc.sql_db:
            path = filedialog.asksaveasfilename(
                title="Choose or Create a SQLite Database", confirmoverwrite=False,
                defaultextension=".db",
                filetypes=[("All files", "*.*"), ("SQLite databases", "*.db *.sqlite *.sqlite3")])
            if not path:
                return
            doc.sql_db = path
        sql = w.get("sel.first", "sel.last") if w.tag_ranges("sel") else doc.content()
        statements = []
        buffer = ""
        for line in sql.split("\n"):
            buffer += line + "\n"
            if sqlite3.complete_statement(buffer):
                if buffer.strip():
                    statements.append(buffer.strip())
                buffer = ""
        if buffer.strip():
            statements.append(buffer.strip())
        self.show_output()
        self.clear_output()
        self._out_append(f"Database: {doc.sql_db}\n", "info")
        result_sets = []
        try:
            con = sqlite3.connect(doc.sql_db)
        except sqlite3.Error as e:
            self._out_append(f"Could not open the database: {e}\n", "error")
            doc.sql_db = None
            return
        try:
            for statement in statements:
                started = time.monotonic()
                try:
                    cur = con.execute(statement)
                    if cur.description:
                        rows = cur.fetchmany(10000)
                        cols = [d[0] for d in cur.description]
                        result_sets.append((statement, cols, rows))
                        info = f"{len(rows):,} row(s)"
                    else:
                        info = f"{cur.rowcount if cur.rowcount >= 0 else 0:,} row(s) affected"
                    ms = (time.monotonic() - started) * 1000
                    first = statement.split("\n")[0][:80]
                    self._out_append(f"OK   {first}   -> {info} ({ms:.0f} ms)\n")
                except sqlite3.Error as e:
                    self._out_append(f"ERROR in: {statement[:200]}\n  {e}\n", "error")
                    break
            con.commit()
        finally:
            con.close()
        if result_sets:
            self._show_sql_results(result_sets, doc.sql_db)
        self.set_message(f"Executed {len(statements)} statement(s) on {os.path.basename(doc.sql_db)}")

    def _show_sql_results(self, result_sets, db):
        win = tk.Toplevel(self.root)
        win.title(f"SQL Results - {os.path.basename(db)}")
        win.geometry("900x500")
        nb = ttk.Notebook(win)
        nb.pack(fill="both", expand=True)
        for i, (statement, cols, rows) in enumerate(result_sets, 1):
            frame = tk.Frame(nb)
            nb.add(frame, text=f"Result {i} ({len(rows):,})")
            tk.Label(frame, text=statement.split("\n")[0][:150], anchor="w", fg="gray").pack(
                fill="x")
            ids = [f"c{k}" for k in range(len(cols))]
            tree = ttk.Treeview(frame, columns=ids, show="headings")
            ys = ttk.Scrollbar(frame, command=tree.yview)
            xs = ttk.Scrollbar(frame, orient="horizontal", command=tree.xview)
            tree.config(yscrollcommand=ys.set, xscrollcommand=xs.set)
            ys.pack(side="right", fill="y")
            xs.pack(side="bottom", fill="x")
            tree.pack(fill="both", expand=True)
            for c, name in zip(ids, cols):
                tree.heading(c, text=name)
                tree.column(c, width=max(80, min(260, self.font.measure(str(name)) + 30)),
                            stretch=False)
            for row in rows:
                tree.insert("", "end", values=["NULL" if v is None else
                                               (f"<{len(v)} bytes>" if isinstance(v, bytes) else v)
                                               for v in row])
        win.bind("<Escape>", lambda e: win.destroy())

    def _serve_preview(self, path, content, suffix):
        folder = os.path.dirname(path)
        name = os.path.basename(path) + suffix
        if not self.preview_server or self.preview_server.root_folder != folder:
            if self.preview_server:
                threading.Thread(target=self.preview_server.shutdown, daemon=True).start()
            cache = self.preview_cache

            class Handler(http.server.SimpleHTTPRequestHandler):
                def __init__(self, *args, **kwargs):
                    super().__init__(*args, directory=folder, **kwargs)

                def do_GET(self):
                    key = urllib.parse.unquote(urllib.parse.urlparse(self.path).path).lstrip("/")
                    if key in cache:
                        data = cache[key].encode("utf-8")
                        self.send_response(200)
                        self.send_header("Content-Type", "text/html; charset=utf-8")
                        self.send_header("Content-Length", str(len(data)))
                        self.send_header("Cache-Control", "no-store")
                        self.end_headers()
                        self.wfile.write(data)
                        return
                    super().do_GET()

                def log_message(self, *args):
                    pass

            try:
                server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
            except OSError:
                return None
            server.root_folder = folder
            server.daemon_threads = True
            threading.Thread(target=server.serve_forever, daemon=True).start()
            self.preview_server = server
            self.preview_cache.clear()
        self.preview_cache[name] = content
        port = self.preview_server.server_address[1]
        return f"http://127.0.0.1:{port}/{urllib.parse.quote(name)}"

    def export_html_file(self):
        doc = self.current()
        if not doc or doc.kind != "text":
            return
        path = filedialog.asksaveasfilename(title="Export as HTML", defaultextension=".html",
                                            initialfile=os.path.splitext(doc.name())[0] + ".html",
                                            filetypes=[("All files", "*.*"), ("HTML", "*.html")])
        if not path:
            return
        numbers = messagebox.askyesno(APP, "Include line numbers?")
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(export_html(doc.content(), doc.lang, self.theme, doc.name(), numbers))
        except OSError as e:
            messagebox.showerror("Error", str(e))
            return
        self.set_message(f"Exported to {path}")
        if messagebox.askyesno(APP, "Open it in the browser?"):
            webbrowser.open(Path(path).as_uri())

    def export_pdf_file(self):
        doc = self.current()
        if not doc or doc.kind != "text":
            return
        path = filedialog.asksaveasfilename(title="Export as PDF", defaultextension=".pdf",
                                            initialfile=os.path.splitext(doc.name())[0] + ".pdf",
                                            filetypes=[("All files", "*.*"), ("PDF", "*.pdf")])
        if not path:
            return
        numbers = messagebox.askyesno(APP, "Include line numbers?")
        try:
            with open(path, "wb") as f:
                f.write(build_pdf(doc.content(), doc.name(), numbers=numbers, header=True))
        except OSError as e:
            messagebox.showerror("Error", str(e))
            return
        self.set_message(f"Exported to {path} (uses the built-in Courier font; characters it "
                         "cannot show become '?')")

    def compare_folders(self):
        left = filedialog.askdirectory(title="Compare Folders: first folder")
        if not left:
            return
        right = filedialog.askdirectory(title="Compare Folders: second folder")
        if not right:
            return
        win = tk.Toplevel(self.root)
        win.title(f"Compare: {left}  <->  {right}")
        win.geometry("820x520")
        tree = ttk.Treeview(win, columns=("status",))
        tree.heading("#0", text="File")
        tree.heading("status", text="Status")
        tree.column("status", width=200)
        sb = ttk.Scrollbar(win, command=tree.yview)
        tree.config(yscrollcommand=sb.set)
        summary = tk.Label(win, anchor="w")
        summary.pack(side="bottom", fill="x", padx=6, pady=4)
        sb.pack(side="right", fill="y")
        tree.pack(fill="both", expand=True)
        tree.tag_configure("diff", foreground="#C07000")
        tree.tag_configure("left", foreground="#C72E2E")
        tree.tag_configure("right", foreground="#098658")
        counts = {"same": 0, "diff": 0, "left": 0, "right": 0}
        pairs = {}

        def walk(cmp, rel):
            for name in sorted(cmp.diff_files):
                node = tree.insert("", "end", text=os.path.join(rel, name), values=("Different",),
                                   tags=("diff",))
                pairs[node] = (os.path.join(cmp.left, name), os.path.join(cmp.right, name))
                counts["diff"] += 1
            for name in sorted(cmp.left_only):
                tree.insert("", "end", text=os.path.join(rel, name),
                            values=("Only in first folder",), tags=("left",))
                counts["left"] += 1
            for name in sorted(cmp.right_only):
                tree.insert("", "end", text=os.path.join(rel, name),
                            values=("Only in second folder",), tags=("right",))
                counts["right"] += 1
            counts["same"] += len(cmp.same_files)
            for name, sub in sorted(cmp.subdirs.items()):
                if name not in SKIP_DIRS:
                    walk(sub, os.path.join(rel, name))

        try:
            walk(filecmp.dircmp(left, right, ignore=list(SKIP_DIRS)), "")
        except OSError as e:
            messagebox.showerror("Error", str(e))
        summary.config(text=f"{counts['diff']} different, {counts['left']} only in first, "
                            f"{counts['right']} only in second, {counts['same']} identical. "
                            "Double-click a different file to see the changes.")

        def show(event=None):
            sel = tree.selection()
            if sel and sel[0] in pairs:
                a, b = pairs[sel[0]]
                ta, tb = self._read(a), self._read(b)
                if ta and tb:
                    norm = lambda s: s.replace("\r\n", "\n").replace("\r", "\n")
                    self._show_diff(a, norm(ta[0]), b, norm(tb[0]))

        tree.bind("<Double-Button-1>", show)
        win.bind("<Escape>", lambda e: win.destroy())

    def todo_list(self):
        doc = self.current()
        scope_folder = messagebox.askyesnocancel(
            APP, "Search TODO / FIXME / HACK / XXX / NOTE comments in the whole folder?\n\n"
                 "Yes: the folder of the current file.\nNo: only the current document.")
        if scope_folder is None:
            return
        pattern = re.compile(r"\b(TODO|FIXME|HACK|XXX|NOTE|BUG)\b[:\s]*(.*)")
        items = []
        if scope_folder:
            folder = os.path.dirname(doc.path) if doc and doc.path else self.explorer_root
            for path, number, line, col in self._fif_walk(folder, ["*"], pattern):
                items.append((path, number, line.strip()))
                if len(items) >= FIF_MAX_RESULTS:
                    break
            items = [i for i in items if i is not None]
        elif doc:
            for n, line in enumerate(doc.content().split("\n"), 1):
                if pattern.search(line):
                    items.append((doc, n, line.strip()))
        items = [i for i in items if i]
        if not items:
            messagebox.showinfo(APP, "No TODO comments found.")
            return
        win = tk.Toplevel(self.root)
        win.title(f"TODO List ({len(items)})")
        win.geometry("820x420")
        lb = tk.Listbox(win, font=self.font)
        sb = tk.Scrollbar(win, command=lb.yview)
        lb.config(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        lb.pack(fill="both", expand=True)
        for owner, n, text in items:
            name = owner.name() if isinstance(owner, Document) else os.path.relpath(
                owner, os.path.dirname(doc.path) if doc and doc.path else self.explorer_root)
            lb.insert("end", f"{name}:{n}   {text[:150]}")

        def go(event=None):
            sel = lb.curselection()
            if sel:
                owner, n, _ = items[sel[0]]
                if isinstance(owner, Document):
                    self._goto(owner, n)
                else:
                    self.open_file(owner, line=n)

        lb.bind("<Double-Button-1>", go)
        lb.bind("<Return>", go)
        win.bind("<Escape>", lambda e: win.destroy())

    def convert_folder_utf8(self):
        folder = filedialog.askdirectory(title="Convert Folder to UTF-8")
        if not folder:
            return
        pattern = simpledialog.askstring("Convert to UTF-8", "Files to convert (patterns):",
                                         initialvalue="*.txt *.csv *.md *.html *.py *.ini",
                                         parent=self.root)
        if not pattern:
            return
        globs = pattern.split()
        targets = []
        for dirpath, dirnames, filenames in os.walk(folder):
            dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
            for name in filenames:
                if not any(fnmatch.fnmatch(name.lower(), g.lower()) for g in globs):
                    continue
                path = os.path.join(dirpath, name)
                try:
                    with open(path, "rb") as f:
                        data = f.read()
                except OSError:
                    continue
                if looks_binary(data):
                    continue
                text, enc = decode_bytes(data)
                if enc not in ("utf-8",):
                    targets.append((path, text, enc))
        if not targets:
            messagebox.showinfo(APP, "All matching files are already UTF-8.")
            return
        listing = "\n".join(f"{os.path.relpath(p, folder)} ({e})" for p, _, e in targets[:25])
        more = f"\n... and {len(targets) - 25} more" if len(targets) > 25 else ""
        if not messagebox.askyesno(APP, f"Convert {len(targets)} file(s) to UTF-8?\n\n"
                                        f"{listing}{more}\n\nA copy of each original is kept in "
                                        "Local History."):
            return
        done = 0
        for path, text, enc in targets:
            try:
                self.add_history_version(path, text)
                with open(path, "w", encoding="utf-8", newline="") as f:
                    f.write(text)
                done += 1
                existing = self._find_open(path)
                if existing and not existing.modified():
                    self.reload(existing, ask=False)
            except OSError:
                pass
        messagebox.showinfo(APP, f"Converted {done} file(s) to UTF-8.")

    def _fif_pattern(self):
        term = self.fif_text.get()
        if not term:
            return None
        try:
            return re.compile(term if self.fif_regex.get() else re.escape(term),
                              0 if self.fif_case.get() else re.IGNORECASE)
        except re.error as e:
            self.fif_status.config(text=f"Invalid regular expression: {e}")
            return None

    def _fif_preview_replace(self):
        self._fif_stop()
        pattern = self._fif_pattern()
        folder = self.fif_folder.get()
        if not pattern or not os.path.isdir(folder):
            return
        repl = self.fif_replace.get()
        globs = [g for g in re.split(r"[;,\s]+", self.fif_glob.get()) if g] or ["*"]
        changes = {}
        self.fif_list.delete(0, "end")
        self._fif_results = []
        total = 0
        for item in self._fif_walk(folder, globs, pattern):
            if item is None:
                continue
            path, number, line, col = item
            try:
                new_line = pattern.sub(lambda m: m.expand(repl) if self.fif_regex.get() else repl,
                                       line)
            except (re.error, IndexError) as e:
                self.fif_status.config(text=f"Bad replacement: {e}")
                return
            changes.setdefault(path, []).append(number)
            rel = os.path.relpath(path, folder)
            self.fif_list.insert("end", f"{rel}:{number}:  {line.strip()[:90]}   →   "
                                        f"{new_line.strip()[:90]}")
            self._fif_results.append((path, number, col))
            total += 1
            if total >= FIF_MAX_RESULTS:
                break
        self._fif_preview = (pattern, repl, self.fif_regex.get(), list(changes))
        self.fif_apply.config(state="normal" if changes else "disabled")
        self.fif_status.config(text=f"{total:,} change(s) in {len(changes):,} file(s). Review "
                                    "them and press Apply Replace.")

    def _fif_apply_replace(self):
        if not self._fif_preview:
            return
        pattern, repl, use_regex, files = self._fif_preview
        if not messagebox.askyesno(APP, f"Replace in {len(files)} file(s)?\nOriginals are kept "
                                        "in Local History.", parent=self.fif_win):
            return
        changed = skipped = 0
        for path in files:
            open_doc = self._find_open(path)
            if open_doc and open_doc.modified():
                skipped += 1
                continue
            try:
                with open(path, "rb") as f:
                    data = f.read()
                text, enc = decode_bytes(data)
                new = pattern.sub(lambda m: m.expand(repl) if use_regex else repl, text)
                if new != text:
                    self.add_history_version(path, text.replace("\r\n", "\n"))
                    with open(path, "wb") as f:
                        f.write(new.encode(enc))
                    changed += 1
                    if open_doc:
                        self.reload(open_doc, ask=False)
            except (OSError, UnicodeEncodeError, re.error, IndexError):
                skipped += 1
        self._fif_preview = None
        self.fif_apply.config(state="disabled")
        self.fif_status.config(text=f"Replaced in {changed} file(s); {skipped} skipped "
                                    "(unsaved changes or errors).")

    def git_refresh(self, doc):
        doc.git_base = None
        doc.git_branch = None
        doc.git_marks = {}
        if not doc.path or doc.kind != "text":
            return
        folder = os.path.dirname(doc.path)
        branch = git_run(["rev-parse", "--abbrev-ref", "HEAD"], folder)
        if branch is None:
            return
        doc.git_branch = branch.decode("utf-8", errors="replace").strip()
        data = git_run(["show", f"HEAD:./{os.path.basename(doc.path)}"], folder)
        if data is not None:
            text = decode_bytes(data)[0].replace("\r\n", "\n").replace("\r", "\n")
            doc.git_base = text.split("\n")
        else:
            doc.git_base = []
        self.git_marks(doc, doc.content())
        if self.current() is doc:
            self.update_status()

    def git_marks(self, doc, content):
        base = doc.git_base
        marks = {}
        lines = content.split("\n")
        if base is not None and len(lines) <= GIT_MAX_LINES and len(base) <= GIT_MAX_LINES:
            if not base:
                marks = {n: "add" for n in range(1, len(lines) + 1)}
            else:
                matcher = difflib.SequenceMatcher(None, base, lines, autojunk=False)
                for op, i1, i2, j1, j2 in matcher.get_opcodes():
                    if op == "insert":
                        for n in range(j1, j2):
                            marks[n + 1] = "add"
                    elif op == "replace":
                        for n in range(j1, j2):
                            marks[n + 1] = "mod"
                    elif op == "delete":
                        marks[max(1, j1)] = marks.get(max(1, j1), "del")
        if marks != doc.git_marks:
            doc.git_marks = marks
            doc.redraw_gutter()

    def show_git_status(self):
        doc = self.current()
        if not doc or not doc.path:
            return
        out = git_run(["status", "--short", "--branch"], os.path.dirname(doc.path))
        if out is None:
            return
        self.show_output()
        self.clear_output()
        self._out_append(out.decode("utf-8", errors="replace") or "Nothing to commit\n")

    def apply_ttk_theme(self):
        th = self.theme
        st = self.style
        try:
            scale = int(self.ui_scale.get()) / 100
        except ValueError:
            scale = 1.0
        for name, bg in (("Closable.TNotebook", th["tabbar_bg"]), ("Panel.TNotebook", th["bg"])):
            st.configure(name, background=bg, borderwidth=0, tabmargins=(0, 0, 0, 0),
                         lightcolor=bg, darkcolor=bg, bordercolor=th["border"])
        st.configure("Closable.TNotebook.Tab", background=th["tab_inactive_bg"],
                     foreground=th["tab_inactive_fg"], borderwidth=0, padding=(12, 6, 8, 6),
                     lightcolor=th["tab_inactive_bg"], darkcolor=th["tab_inactive_bg"],
                     bordercolor=th["border"], focuscolor=th["tab_inactive_bg"])
        st.map("Closable.TNotebook.Tab",
               background=[("selected", th["bg"]), ("active", th["tab_hover_bg"])],
               foreground=[("selected", th["fg"])],
               lightcolor=[("selected", th["bg"]), ("active", th["tab_hover_bg"])],
               darkcolor=[("selected", th["bg"]), ("active", th["tab_hover_bg"])],
               bordercolor=[("selected", th["border"])], expand=[("selected", (0, 0, 0, 0))])
        st.configure("Panel.TNotebook.Tab", background=th["bg"], foreground=th["tab_inactive_fg"],
                     borderwidth=0, padding=(12, 5, 12, 5), lightcolor=th["bg"],
                     darkcolor=th["bg"], bordercolor=th["bg"], focuscolor=th["bg"],
                     font=("TkDefaultFont", max(8, round(9 * scale))))
        st.map("Panel.TNotebook.Tab", background=[("selected", th["bg"])],
               foreground=[("selected", th["fg"])], lightcolor=[("selected", th["accent"])],
               expand=[("selected", (0, 0, 0, 0))])
        for prefix, trough in (("Editor", th["bg"]), ("Side", th["side_bg"])):
            for orient in ("Vertical", "Horizontal"):
                name = f"{prefix}.{orient}.TScrollbar"
                st.configure(name, troughcolor=trough, background=th["scroll_thumb"],
                             bordercolor=trough, lightcolor=th["scroll_thumb"],
                             darkcolor=th["scroll_thumb"], arrowcolor=th["fg"], gripcount=0,
                             arrowsize=max(10, round(12 * scale)), relief="flat")
                st.map(name, background=[("active", th["scroll_thumb_hover"]),
                                         ("pressed", th["scroll_thumb_hover"])],
                       lightcolor=[("active", th["scroll_thumb_hover"])],
                       darkcolor=[("active", th["scroll_thumb_hover"])])
        st.configure("Side.Treeview", background=th["side_bg"], fieldbackground=th["side_bg"],
                     foreground=th["side_fg"], borderwidth=0, relief="flat",
                     rowheight=max(18, round(22 * scale)), indent=max(10, round(12 * scale)),
                     lightcolor=th["side_bg"], darkcolor=th["side_bg"], bordercolor=th["side_bg"])
        st.map("Side.Treeview", background=[("selected", th["list_sel"])],
               foreground=[("selected", th["fg"])])
        st.configure("Treeview", rowheight=max(18, round(20 * scale)))

    def _build_activity_bar(self):
        bar = tk.Frame(self.root, bd=0, width=48)
        self.activity_bar = bar
        self.activity_buttons = {}
        for name, tip, func in (("files", "Explorer (Ctrl+Shift+E)", self.activity_explorer),
                                ("search", "Find in Folder (Ctrl+Shift+F)", self.find_in_folder),
                                ("outline", "Outline (Ctrl+Shift+J)", self.activity_outline),
                                ("run", "Run File (Ctrl+R)", self.run_file)):
            self._activity_button(bar, name, tip, func).pack(side="top", fill="x")
        self._activity_button(bar, "settings", "Settings (Ctrl+,)",
                              self.settings_window).pack(side="bottom", fill="x", pady=(0, 6))
        bar.pack(side="left", fill="y")

    def _activity_button(self, parent, name, tip, func):
        holder = tk.Frame(parent, bd=0)
        marker = tk.Frame(holder, width=2, bd=0)
        marker.pack(side="left", fill="y")
        label = tk.Label(holder, bd=0, padx=10, pady=10, cursor="hand2")
        label.pack(side="left")
        label.bind("<Button-1>", lambda e: func())
        label.bind("<Enter>", lambda e: self._activity_hover(name, True))
        label.bind("<Leave>", lambda e: self._activity_hover(name, False))
        self._tooltip_for(label, tip)
        self.activity_buttons[name] = (holder, marker, label)
        return holder

    def _tooltip_for(self, widget, text):
        state = {"job": None, "win": None}

        def show():
            state["job"] = None
            label_text = text() if callable(text) else text
            if not label_text:
                return
            win = tk.Toplevel(self.root)
            win.overrideredirect(True)
            x = widget.winfo_rootx() + widget.winfo_width() + 4
            y = widget.winfo_rooty() + widget.winfo_height() // 2 - 10
            win.geometry(f"+{x}+{y}")
            th = self.theme
            tk.Label(win, text=label_text, bg=th["side_bg"], fg=th["fg"], bd=1, relief="solid",
                     padx=6, pady=2).pack()
            state["win"] = win

        def enter(event):
            state["job"] = widget.after(600, show)

        def leave(event):
            if state["job"]:
                widget.after_cancel(state["job"])
                state["job"] = None
            if state["win"]:
                state["win"].destroy()
                state["win"] = None

        widget.bind("<Enter>", enter, add="+")
        widget.bind("<Leave>", leave, add="+")
        widget.bind("<ButtonPress>", leave, add="+")

    def _activity_hover(self, name, inside):
        self._activity_hovered = name if inside else None
        self.refresh_activity_bar()

    def refresh_activity_bar(self):
        th = self.theme
        self.activity_bar.config(bg=th["activity_bg"])
        view = self.side_view()
        hovered = getattr(self, "_activity_hovered", None)
        for name, (holder, marker, label) in self.activity_buttons.items():
            active = (name == "files" and view == "explorer") or (name == "outline"
                                                                    and view == "outline")
            color = th["activity_active"] if active or hovered == name else th["activity_fg"]
            label.config(image=draw_icon(self.root, 24, [(ICON_SHAPES[name], color)],
                                         th["activity_bg"]), bg=th["activity_bg"])
            holder.config(bg=th["activity_bg"])
            marker.config(bg=th["activity_active"] if active else th["activity_bg"])

    def activity_explorer(self):
        self.set_side_view(None if self.side_view() == "explorer" else "explorer")

    def activity_outline(self):
        self.set_side_view(None if self.side_view() == "outline" else "outline")

    def side_view(self):
        if self.explorer_var.get():
            return "explorer"
        if self.outline_var.get():
            return "outline"
        return None

    def set_side_view(self, view):
        self.explorer_var.set(view == "explorer")
        self.outline_var.set(view == "outline")
        self.update_side_panel()

    def _on_explorer_check(self):
        self.set_side_view("explorer" if self.explorer_var.get() else None)

    def _on_outline_check(self):
        self.set_side_view("outline" if self.outline_var.get() else None)

    def _side_button(self, parent, icon, tip, func):
        label = tk.Label(parent, bd=0, padx=3, pady=3, cursor="hand2")
        label.icon_name = icon
        label.bind("<Button-1>", lambda e: func())
        label.bind("<Enter>", lambda e: label.config(bg=self.theme["list_hover"]))
        label.bind("<Leave>", lambda e: label.config(bg=self.theme["side_bg"]))
        self._tooltip_for(label, tip)
        label.pack(side="right", padx=1)
        self.side_buttons.append(label)
        return label

    def _build_side_panel(self):
        self.side_buttons = []
        self.side_panel = tk.Frame(self.hpane, bd=0)
        header = tk.Frame(self.side_panel, bd=0)
        header.pack(fill="x")
        self.side_header = header
        self.side_title = tk.Label(header, text="EXPLORER", anchor="w", padx=12, pady=7,
                                   font=("TkDefaultFont", 9, "bold"))
        self.side_title.pack(side="left", fill="x", expand=True)
        self._side_button(header, "close", "Close Side Bar", lambda: self.set_side_view(None))
        self.explorer_actions = [
            self._side_button(header, "collapse", "Collapse Folders", self.explorer_collapse_all),
            self._side_button(header, "refresh", "Refresh Explorer", self.refresh_explorer),
            self._side_button(header, "up", "Go Up One Folder", self.explorer_up),
            self._side_button(header, "new_folder", "New Folder...",
                              lambda: self.explorer_new(folder=True)),
            self._side_button(header, "new_file", "New File...",
                              lambda: self.explorer_new(folder=False)),
        ]
        self.outline_actions = [
            self._side_button(header, "collapse", "Collapse All", self.outline_collapse_all),
            self._side_button(header, "expand_all", "Expand All", self.outline_expand_all),
        ]
        self.side_body = tk.Frame(self.side_panel, bd=0)
        self.side_body.pack(fill="both", expand=True)

        ex = tk.Frame(self.side_body, bd=0)
        self.explorer_root_label = tk.Label(ex, anchor="w", padx=8, pady=3, cursor="hand2",
                                            font=("TkDefaultFont", 9, "bold"))
        self.explorer_root_label.pack(fill="x")
        self.explorer_root_label.bind("<Button-1>", lambda e: self.open_folder_explorer())
        self._tooltip_for(self.explorer_root_label,
                          lambda: f"{self.explorer_root}\n(click to open another folder)")
        body = tk.Frame(ex, bd=0)
        body.pack(fill="both", expand=True)
        self.explorer = ttk.Treeview(body, show="tree", columns=("status",),
                                     selectmode="browse", style="Side.Treeview")
        self.explorer.column("#0", stretch=True, width=200)
        self.explorer.column("status", width=24, stretch=False, anchor="center")
        sb = ttk.Scrollbar(body, command=self.explorer.yview, style="Side.Vertical.TScrollbar")
        self.explorer.config(yscrollcommand=lambda f, l: self._autohide(sb, self.explorer, f, l))
        sb.pack(side="right", fill="y")
        self.explorer.pack(side="left", fill="both", expand=True)
        self.explorer.bind("<<TreeviewOpen>>", self._explorer_open_node)
        self.explorer.bind("<ButtonRelease-1>", self._explorer_click)
        self.explorer.bind("<Return>", self._explorer_activate)
        self.explorer.bind("<Motion>", self._explorer_hover)
        self.explorer.bind("<Leave>", lambda e: self._tree_hover(self.explorer, None))
        self.explorer.bind("<Button-2>" if self.aqua else "<Button-3>", self._explorer_menu)
        self.explorer_frame = ex
        self.explorer_paths = {}

        ol = tk.Frame(self.side_body, bd=0)
        self.outline_doc_label = tk.Label(ol, anchor="w", padx=8, pady=3,
                                          font=("TkDefaultFont", 9, "bold"))
        self.outline_doc_label.pack(fill="x")
        body2 = tk.Frame(ol, bd=0)
        body2.pack(fill="both", expand=True)
        self.outline = ttk.Treeview(body2, show="tree", selectmode="browse",
                                    style="Side.Treeview")
        sb2 = ttk.Scrollbar(body2, command=self.outline.yview, style="Side.Vertical.TScrollbar")
        self.outline.config(yscrollcommand=lambda f, l: self._autohide(sb2, self.outline, f, l))
        sb2.pack(side="right", fill="y")
        self.outline.pack(side="left", fill="both", expand=True)
        self.outline.bind("<ButtonRelease-1>", self._outline_select)
        self.outline.bind("<Return>", self._outline_select)
        self.outline.bind("<Motion>", lambda e: self._tree_hover(
            self.outline, self.outline.identify_row(e.y)))
        self.outline.bind("<Leave>", lambda e: self._tree_hover(self.outline, None))
        self.outline_frame = ol
        self.side_visible = False
        self.side_current = None
        self.explorer_root = self.cfg.get("explorer_root") or ""
        self.git_status = {}
        self.apply_side_theme()

    @staticmethod
    def _autohide(scrollbar, widget, first, last):
        scrollbar.set(first, last)
        if float(first) <= 0.0 and float(last) >= 1.0:
            if scrollbar.winfo_manager():
                scrollbar.pack_forget()
        elif not scrollbar.winfo_manager():
            scrollbar.pack(side="right", fill="y", before=widget)

    def apply_side_theme(self):
        th = self.theme
        bg = th["side_bg"]
        for w in (self.side_panel, self.side_header, self.side_body, self.explorer_frame,
                  self.outline_frame):
            w.config(bg=bg)
        for w in self.explorer_frame.winfo_children() + self.outline_frame.winfo_children():
            if isinstance(w, tk.Frame):
                w.config(bg=bg)
        self.side_title.config(bg=bg, fg=th["side_header"])
        for label in (self.explorer_root_label, self.outline_doc_label):
            label.config(bg=bg, fg=th["side_fg"])
        for button in self.side_buttons:
            button.config(bg=bg, image=draw_icon(self.root, 16, [(ICON_SHAPES[button.icon_name],
                                                                 th["side_header"])], bg))
        for tree in (self.explorer, self.outline):
            tree.tag_configure("hover", background=th["list_hover"])
            tree.tag_configure("dim", foreground=th["side_header"])
        self.explorer.tag_configure("git_mod", foreground=th["git_mod_fg"])
        self.explorer.tag_configure("git_new", foreground=th["git_new_fg"])
        self.explorer.tag_configure("git_del", foreground=th["git_del_fg"])
        self.explorer.tag_configure("git_ign", foreground=th["git_ign_fg"])
        self.hpane.config(bg=th["border"])
        self.main_pane.config(bg=th["border"])
        self.refresh_activity_bar()
        if self.explorer.get_children():
            self._explorer_reicon("")
        if self.outline.get_children():
            self.refresh_outline()

    def update_side_panel(self, save=True):
        view = self.side_view() if not self.zen else None
        if view and self.side_current != view:
            for frame in (self.explorer_frame, self.outline_frame):
                frame.pack_forget()
            frame = self.explorer_frame if view == "explorer" else self.outline_frame
            frame.pack(fill="both", expand=True)
            self.side_title.config(text=view.upper())
            for button in self.side_buttons:
                button.pack_forget()
            self.side_buttons[0].pack(side="right", padx=(1, 6))
            for button in (self.explorer_actions if view == "explorer" else self.outline_actions):
                button.pack(side="right", padx=1)
            self.side_current = view
        if view and not self.side_visible:
            width = int(self.cfg.get("side_width") or 250)
            self.hpane.add(self.side_panel, before=self.main_pane, width=width, stretch="never")
            self.side_visible = True
        elif not view and self.side_visible:
            try:
                self.cfg["side_width"] = self.side_panel.winfo_width()
            except tk.TclError:
                pass
            self.hpane.forget(self.side_panel)
            self.side_visible = False
            self.side_current = None
        if view == "explorer":
            if not self.explorer_root or not os.path.isdir(self.explorer_root):
                doc = self.current()
                self.explorer_root = (os.path.dirname(doc.path) if doc and doc.path
                                      else os.path.expanduser("~"))
            if not self.explorer.get_children():
                self.refresh_explorer()
            self.explorer_reveal(self.current())
        elif view == "outline":
            self.refresh_outline()
        self.refresh_activity_bar()
        if save:
            self.save_config()

    def set_explorer_root(self, folder):
        self.explorer_root = os.path.abspath(folder)
        self.cfg["explorer_root"] = self.explorer_root
        self.explorer_var.set(True)
        self.outline_var.set(False)
        self.refresh_explorer()
        self.update_side_panel()

    def open_folder_explorer(self):
        folder = filedialog.askdirectory(title="Open Folder",
                                         initialdir=self.explorer_root or os.path.expanduser("~"))
        if folder:
            self.set_explorer_root(folder)

    def explorer_up(self):
        parent = os.path.dirname(self.explorer_root)
        if parent and parent != self.explorer_root:
            self.set_explorer_root(parent)

    def explorer_collapse_all(self):
        def collapse(node):
            for child in self.explorer.get_children(node):
                self.explorer.item(child, open=False)
                collapse(child)
        collapse("")

    def outline_collapse_all(self):
        for node in self.outline.get_children():
            self.outline.item(node, open=False)

    def outline_expand_all(self):
        def expand(node):
            for child in self.outline.get_children(node):
                self.outline.item(child, open=True)
                expand(child)
        expand("")

    def _file_image(self, name, is_dir=False, opened=False, up=False):
        th = self.theme
        if is_dir or up:
            layers = folder_icon_layers(th["folder"], opened, up)
        else:
            layers = file_icon_layers(name)
        return draw_icon(self.root, 16, layers, th["side_bg"])

    def refresh_explorer(self):
        tree = self.explorer
        opened = {self.explorer_paths.get(n) for n in self._all_nodes(tree)
                  if tree.item(n, "open")}
        tree.delete(*tree.get_children())
        self.explorer_paths = {}
        root = self.explorer_root
        if not root or not os.path.isdir(root):
            root = self.explorer_root = os.path.expanduser("~")
        self.explorer_root_label.config(text="∨  " + (os.path.basename(root) or root).upper())
        self.load_git_status()
        parent = os.path.dirname(root)
        if parent and parent != root:
            node = tree.insert("", "end", text="  ..", image=self._file_image("", up=True),
                               tags=("dim",))
            self.explorer_paths[node] = ".."
        self._explorer_fill("", root)
        for node in list(self._all_nodes(tree)):
            if self.explorer_paths.get(node) in opened:
                self._explorer_expand(node)

    def _all_nodes(self, tree, parent=""):
        for node in tree.get_children(parent):
            yield node
            yield from self._all_nodes(tree, node)

    def load_git_status(self):
        self.git_status = {}
        root = self.explorer_root
        top = git_run(["rev-parse", "--show-toplevel"], root)
        if top is None:
            return
        top = top.decode("utf-8", errors="replace").strip()
        out = git_run(["status", "--porcelain=v1", "-uall", "--ignored=matching"], root)
        if out is None:
            return
        for line in out.decode("utf-8", errors="replace").splitlines():
            if len(line) < 4:
                continue
            code, rel = line[:2], line[3:].split(" -> ")[-1].strip('"')
            full = os.path.normcase(os.path.normpath(os.path.join(top, rel)))
            if code == "!!":
                status = "ign"
            elif "?" in code or "A" in code:
                status = "new"
            elif "D" in code:
                status = "del"
            else:
                status = "mod"
            self.git_status[full] = status
            if status != "ign":
                folder = os.path.dirname(full)
                while len(folder) >= len(os.path.normcase(top)) and folder not in ("", "/"):
                    self.git_status.setdefault(folder, "dirty" if status != "new" else "dirty_new")
                    nxt = os.path.dirname(folder)
                    if nxt == folder:
                        break
                    folder = nxt

    def _git_decor(self, path):
        key = os.path.normcase(os.path.normpath(path))
        status = self.git_status.get(key)
        if status is None:
            for ignored, value in self.git_status.items():
                if value == "ign" and key.startswith(ignored.rstrip("/\\") + os.sep):
                    return ("git_ign",), ""
            return (), ""
        return {"mod": (("git_mod",), "M"), "new": (("git_new",), "U"),
                "del": (("git_del",), "D"), "ign": (("git_ign",), ""),
                "dirty": (("git_mod",), "•"), "dirty_new": (("git_new",), "•")}[status]

    def _explorer_fill(self, parent, folder):
        try:
            entries = sorted(os.scandir(folder), key=lambda e: (not e.is_dir(), e.name.lower()))
        except OSError:
            return
        for entry in entries:
            if entry.is_dir() and entry.name in (".git", ".hg", ".svn", "__pycache__"):
                continue
            is_dir = entry.is_dir()
            tags, mark = self._git_decor(entry.path)
            node = self.explorer.insert(parent, "end", text="  " + entry.name,
                                        image=self._file_image(entry.name, is_dir),
                                        values=(mark,), tags=tags)
            self.explorer_paths[node] = entry.path
            if is_dir:
                self.explorer.insert(node, "end", text="", tags=("placeholder",))

    def _explorer_reicon(self, parent):
        for node in self.explorer.get_children(parent):
            path = self.explorer_paths.get(node)
            if not path:
                continue
            if path == "..":
                self.explorer.item(node, image=self._file_image("", up=True))
                continue
            is_dir = os.path.isdir(path)
            opened = bool(self.explorer.item(node, "open"))
            self.explorer.item(node, image=self._file_image(os.path.basename(path), is_dir,
                                                            opened))
            self._explorer_reicon(node)

    def _explorer_expand(self, node):
        children = self.explorer.get_children(node)
        if len(children) == 1 and "placeholder" in self.explorer.item(children[0], "tags"):
            self.explorer.delete(children[0])
            self._explorer_fill(node, self.explorer_paths[node])
        self.explorer.item(node, open=True)
        path = self.explorer_paths.get(node)
        if path:
            self.explorer.item(node, image=self._file_image(os.path.basename(path), True, True))

    def _explorer_open_node(self, event=None):
        node = self.explorer.focus()
        if node and node in self.explorer_paths and os.path.isdir(self.explorer_paths[node]):
            self._explorer_expand(node)

    def _explorer_click(self, event):
        tree = self.explorer
        node = tree.identify_row(event.y)
        if not node:
            return
        path = self.explorer_paths.get(node)
        if path == "..":
            self.explorer_up()
            return
        if not path:
            return
        if "indicator" in tree.identify_element(event.x, event.y):
            if tree.item(node, "open"):
                self._explorer_expand(node)
            else:
                tree.item(node, image=self._file_image(os.path.basename(path), True, False))
            return
        if os.path.isdir(path):
            if tree.item(node, "open"):
                tree.item(node, open=False)
                tree.item(node, image=self._file_image(os.path.basename(path), True, False))
            else:
                self._explorer_expand(node)
        elif os.path.isfile(path):
            self.open_file(path)

    def _explorer_activate(self, event=None):
        node = self.explorer.focus()
        path = self.explorer_paths.get(node)
        if path == "..":
            self.explorer_up()
        elif path and os.path.isdir(path):
            if self.explorer.item(node, "open"):
                self.explorer.item(node, open=False)
            else:
                self._explorer_expand(node)
        elif path and os.path.isfile(path):
            self.open_file(path)
        return "break"

    def _tree_hover(self, tree, node):
        previous = getattr(tree, "_hover_node", None)
        if previous == node:
            return
        if previous and tree.exists(previous):
            tags = [t for t in tree.item(previous, "tags") if t != "hover"]
            tree.item(previous, tags=tags)
        if node:
            tree.item(node, tags=list(tree.item(node, "tags")) + ["hover"])
        tree._hover_node = node

    def _explorer_hover(self, event):
        self._tree_hover(self.explorer, self.explorer.identify_row(event.y) or None)

    def explorer_reveal(self, doc):
        if not doc or not doc.path or self.side_view() != "explorer":
            return
        root = os.path.normcase(os.path.abspath(self.explorer_root))
        target = os.path.normcase(os.path.abspath(doc.path))
        if not target.startswith(root.rstrip(os.sep) + os.sep):
            return
        parts = os.path.relpath(doc.path, self.explorer_root).split(os.sep)
        parent = ""
        path = self.explorer_root
        node = None
        for i, part in enumerate(parts):
            path = os.path.join(path, part)
            node = next((n for n in self.explorer.get_children(parent)
                         if os.path.normcase(self.explorer_paths.get(n, "")) ==
                         os.path.normcase(path)), None)
            if node is None:
                return
            if i < len(parts) - 1:
                self._explorer_expand(node)
            parent = node
        if node:
            self.explorer.selection_set(node)
            self.explorer.focus(node)
            self.explorer.see(node)

    def _explorer_target_folder(self):
        node = self.explorer.focus()
        path = self.explorer_paths.get(node)
        if path and path != ".." and os.path.isdir(path):
            return path
        if path and path != ".." and os.path.isfile(path):
            return os.path.dirname(path)
        return self.explorer_root

    def explorer_new(self, folder=False, base=None):
        base = base or self._explorer_target_folder()
        name = simpledialog.askstring("New Folder" if folder else "New File",
                                      f"Name (inside {os.path.basename(base) or base}):",
                                      parent=self.root)
        if not name:
            return None
        target = os.path.join(base, name)
        if os.path.exists(target):
            messagebox.showerror(APP, f"{name} already exists.")
            return None
        try:
            if folder:
                os.makedirs(target)
            else:
                os.makedirs(os.path.dirname(target), exist_ok=True)
                with open(target, "w", encoding="utf-8"):
                    pass
        except OSError as e:
            messagebox.showerror(APP, str(e))
            return None
        self.refresh_explorer()
        if not folder:
            doc = self.open_file(target)
            self.explorer_reveal(doc)
        return target

    def _explorer_menu(self, event):
        node = self.explorer.identify_row(event.y)
        path = self.explorer_paths.get(node) if node else None
        if path == "..":
            return
        if node:
            self.explorer.selection_set(node)
            self.explorer.focus(node)
        m = tk.Menu(self.root, tearoff=0)
        folder = path if path and os.path.isdir(path) else (
            os.path.dirname(path) if path else self.explorer_root)
        if path and os.path.isfile(path):
            m.add_command(label="Open", command=lambda: self.open_file(path))
            m.add_command(label="Open in New Window", command=lambda: (
                lambda cmd: cmd and subprocess.Popen(cmd))(
                self.relaunch_command("--new-window", path)))
            m.add_separator()
        m.add_command(label="New File...", command=lambda: self.explorer_new(False, folder))
        m.add_command(label="New Folder...", command=lambda: self.explorer_new(True, folder))
        if path:
            m.add_separator()
            m.add_command(label="Rename...", command=lambda: self.explorer_rename(path))
            m.add_command(label="Delete", command=lambda: self.explorer_delete(path))
            m.add_separator()
            m.add_command(label="Copy Path", command=lambda: self._copy(path))
            m.add_command(label="Copy Relative Path", command=lambda: self._copy(
                os.path.relpath(path, self.explorer_root)))
            m.add_command(label="Reveal in File Manager",
                          command=lambda: reveal_in_file_manager(path))
            if os.path.isdir(path):
                m.add_command(label="Open Folder Here", command=lambda: self.set_explorer_root(path))
                m.add_command(label="Find in Folder...", command=lambda: self._fif_in(path))
        m.add_separator()
        m.add_command(label="Refresh", command=self.refresh_explorer)
        try:
            m.tk_popup(event.x_root, event.y_root)
        finally:
            m.grab_release()

    def _fif_in(self, folder):
        self.find_in_folder()
        self.fif_folder.set(folder)

    def explorer_rename(self, path):
        old = os.path.basename(path)
        new = simpledialog.askstring("Rename", "New name:", initialvalue=old, parent=self.root)
        if not new or new == old:
            return
        target = os.path.join(os.path.dirname(path), new)
        if os.path.exists(target):
            messagebox.showerror(APP, f"{new} already exists.")
            return
        try:
            os.rename(path, target)
        except OSError as e:
            messagebox.showerror(APP, str(e))
            return
        for doc in self.docs.values():
            if doc.path and os.path.normcase(doc.path).startswith(os.path.normcase(path)):
                doc.path = target + doc.path[len(path):]
                doc.mtime = os.path.getmtime(doc.path) if os.path.exists(doc.path) else None
                doc.setup_language()
                self.update_tab(doc)
        self.refresh_explorer()

    def explorer_delete(self, path):
        name = os.path.basename(path)
        if os.path.isdir(path):
            try:
                empty = not os.listdir(path)
            except OSError:
                empty = False
            if not empty:
                messagebox.showinfo(APP, f"'{name}' is not empty. To protect your files, delete "
                                         "non-empty folders from your file manager.")
                return
        if not messagebox.askyesno(APP, f"Delete '{name}' permanently?\n\nThis cannot be "
                                        "undone."):
            return
        doc = self._find_open(path)
        try:
            if os.path.isdir(path):
                os.rmdir(path)
            else:
                os.remove(path)
        except OSError as e:
            messagebox.showerror(APP, str(e))
            return
        if doc:
            doc.mtime = None
            doc.text.edit_modified(True)
            self.update_tab(doc)
        self.refresh_explorer()

    def refresh_outline(self):
        if not hasattr(self, "outline") or self.side_view() != "outline":
            return
        doc = self.current()
        tree = self.outline
        tree.delete(*tree.get_children())
        tree._hover_node = None
        self.outline_doc_label.config(text=(doc.name().upper() if doc else ""))
        if not doc or doc.kind != "text":
            return
        stack = [("", -1)]
        bg = self.theme["side_bg"]
        if not doc.symbols:
            tree.insert("", "end", text="  No symbols found in this document", tags=("dim",))
        for sym in doc.symbols:
            while stack and stack[-1][1] >= sym["depth"]:
                stack.pop()
            parent = stack[-1][0] if stack else ""
            image = draw_icon(self.root, 16, symbol_icon_layers(sym["kind"]), bg)
            node = tree.insert(parent, "end", text="  " + sym["name"], image=image,
                               values=(sym["line"],), open=True)
            stack.append((node, sym["depth"]))

    def _outline_select(self, event=None):
        tree = self.outline
        if event is not None and event.type == tk.EventType.ButtonRelease:
            node = tree.identify_row(event.y)
            if not node or "indicator" in tree.identify_element(event.x, event.y):
                return
        else:
            node = tree.focus()
        doc = self.current()
        if node and doc and self.outline.item(node, "values"):
            line = int(self.outline.item(node, "values")[0])
            self._goto(doc, line)
            doc.view().focus_set()

    def _build_console(self):
        f = tk.Frame(self.bottom_nb, bd=0)
        self.console_text = tk.Text(f, height=10, font=self.font, wrap="char", bd=0,
                                    highlightthickness=0, padx=10, pady=4, undo=False)
        sb = ttk.Scrollbar(f, command=self.console_text.yview,
                           style="Editor.Vertical.TScrollbar")
        self.console_text.config(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self.console_text.pack(side="left", fill="both", expand=True)
        self.console_frame = f
        self.bottom_nb.add(f, text="PYTHON CONSOLE")
        self.console = code.InteractiveConsole({"editor": self, "__name__": "__console__"})
        self.console_history = []
        self.console_hpos = 0
        c = self.console_text
        c.bind("<Return>", self._console_enter)
        c.bind("<KP_Enter>", self._console_enter)
        c.bind("<Up>", lambda e: self._console_history(-1))
        c.bind("<Down>", lambda e: self._console_history(1))
        c.bind("<BackSpace>", self._console_backspace)
        c.bind("<Key>", self._console_key, add="+")
        c.bind("<Home>", lambda e: (c.mark_set("insert", "console_input"), "break")[1])
        self._console_write(f"Python {sys.version.split()[0]} - the variable 'editor' is this "
                            "Notepad window.\n", "info")
        self._console_prompt(">>> ")

    def apply_ui_scale(self, save=True):
        try:
            scale = int(self.ui_scale.get()) / 100
        except ValueError:
            scale = 1.0
        for name, base in self._base_fonts.items():
            try:
                tkfont.nametofont(name).configure(size=round(base * scale))
            except tk.TclError:
                pass
        self.apply_ttk_theme()
        if save:
            self.save_config()


def run_self_test():
    import types
    work = tempfile.mkdtemp(prefix="notepad_selftest_")
    configure_paths(os.path.join(work, "config"))
    results = []
    answers = {"string": [], "integer": [], "save": [], "open": [], "dir": [], "yesno": []}
    shown = []
    opened_urls = []

    def check(name, condition, detail=""):
        results.append((name, bool(condition)))
        print(("PASS  " if condition else "FAIL  ") + name +
              ("" if condition or detail == "" else f"   -> {detail!r}"), flush=True)

    def pop(kind, default=None):
        return answers[kind].pop(0) if answers[kind] else default

    messagebox.askyesno = lambda *a, **k: pop("yesno", True)
    messagebox.askyesnocancel = lambda *a, **k: pop("yesno", False)
    messagebox.showinfo = lambda *a, **k: shown.append(("info", a[1] if len(a) > 1 else ""))
    messagebox.showerror = lambda *a, **k: shown.append(("error", a[1] if len(a) > 1 else ""))
    messagebox.showwarning = lambda *a, **k: shown.append(("warn", a[1] if len(a) > 1 else ""))
    simpledialog.askstring = lambda *a, **k: pop("string")
    simpledialog.askinteger = lambda *a, **k: pop("integer")
    filedialog.asksaveasfilename = lambda **k: pop("save", "")
    filedialog.askopenfilename = lambda **k: pop("open", "")
    filedialog.askopenfilenames = lambda **k: tuple(pop("open", []) or [])
    filedialog.askdirectory = lambda **k: pop("dir", "")
    colorchooser.askcolor = lambda **k: ((255, 0, 0), "#ff0000")
    webbrowser.open = lambda url: opened_urls.append(url)

    root = tk.Tk()
    root.geometry("1000x700+20+20")
    app = Notepad(root)

    def pump(n=15):
        for _ in range(n):
            root.update()
            time.sleep(0.01)

    def write(name, data):
        path = os.path.join(work, name)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as f:
            f.write(data if isinstance(data, bytes) else data.encode("utf-8"))
        return path

    def ev(widget):
        return types.SimpleNamespace(widget=widget, state=0, keysym="", char="")

    try:
        py = write("a.py", b"import os\r\ndef f(x):\r\n    return x  \r\n")
        app.start([py + ":2"])
        pump()
        doc = app.current()
        t = doc.text
        check("open file with :line", doc.path == py and t.index("insert").startswith("2."))
        check("CRLF detected and normalized", doc.eol == "\r\n" and "\r" not in doc.content())
        check("python highlighting", doc.lang == "python" and t.tag_ranges("tok_keyword"))
        check("indentation detected", doc.indent_spaces and doc.indent_width == 4)
        check("outline symbols", any(s["name"] == "f" for s in doc.symbols))

        t.mark_set("insert", "1.0")
        doc._on_tab(ev(t))
        check("tab inserts spaces", t.get("1.0", "1.4") == "    ")
        doc._on_shift_tab(ev(t))
        check("shift-tab dedents", t.get("1.0", "1.6") == "import")
        t.mark_set("insert", "2.0")
        app.toggle_comment()
        check("comment line", t.get("2.0", "2.end") == "# def f(x):")
        app.toggle_comment()
        check("uncomment line", t.get("2.0", "2.end") == "def f(x):")
        app.duplicate_line()
        check("duplicate line", t.get("3.0", "3.end") == "def f(x):")
        app.delete_line()
        check("delete line", t.get("3.0", "3.end") == "    return x  ")
        t.mark_set("insert", "1.0")
        app.move_lines(1)
        check("move line down", t.get("2.0", "2.end") == "import os")
        app.move_lines(-1)
        check("move line up", t.get("1.0", "1.end") == "import os")

        t.insert("end", "\nprint")
        t.mark_set("insert", "end-1c")
        doc._on_open_char(ev(t), "(")
        check("auto close paren", t.get("insert-1c", "insert+1c") == "()")
        doc._on_open_char(ev(t), '"')
        check("auto close quote", t.get("insert-1c", "insert+1c") == '""')
        r = doc._on_backspace(ev(t))
        check("backspace removes pair", r == "break" and t.get("insert-1c", "insert+1c") == "()")
        r = doc._on_close_char(ev(t), ")")
        check("type over closing paren", r == "break")

        t.insert("end", "\nmain")
        t.mark_set("insert", "end-1c")
        doc._on_tab(ev(t))
        check("snippet with fields", 'if __name__ == "__main__":' in doc.content()
              and t.tag_ranges("sel") and t.get("sel.first", "sel.last") == "main()")
        doc._on_tab(ev(t))
        check("snippet next field ends session", doc.snippet is None)

        t.insert("end", "\nimpor")
        t.mark_set("insert", "end-1c")
        app.autocomplete()
        check("autocomplete", t.get("insert linestart", "insert") == "import")

        doc.toggle_bookmark(2)
        doc.toggle_bookmark(4)
        t.mark_set("insert", "1.0")
        app.goto_bookmark(1)
        check("next bookmark", t.index("insert").startswith("2."))
        app.nav_go_back()
        check("navigate back", t.index("insert").startswith("1."))
        app.nav_go_forward()
        check("navigate forward", t.index("insert").startswith("2."))

        app.find_var.set("os")
        app.replace_var.set("sys")
        app.replace_all()
        check("replace all", "import sys" in doc.content() and doc.bookmark_lines() == [2, 4])
        t.edit_undo()
        check("undo replace all", "import os" in doc.content())

        app.show_find_bar()
        app.find_var.set("x")
        pump(20)
        app._find_highlight_all()
        check("find bar highlights all", len(t.tag_ranges("find_all")) >= 4
              and "results" in app.find_count.cget("text") or "of" in app.find_count.cget("text"))
        app.hide_find_bar()
        check("find bar closes", not app.find_bar_visible and not t.tag_ranges("find_all"))

        doc2 = app.new_tab()
        t2 = doc2.text
        t2.insert("1.0", "class A:\n    def m(self):\n        return 1\n\nx = 2\n")
        doc2.lang_override = "python"
        doc2.setup_language()
        pump()
        doc2.toggle_fold(1)
        pump()
        box = t2.bbox("2.4")
        check("fold hides block", doc2.fold_starting_at(1) and (box is None or box[2] == 0))
        doc2.toggle_fold(1)
        pump()
        box = t2.bbox("2.4")
        check("unfold shows block", box is not None and box[2] > 0)
        doc2.fold_all()
        check("fold all", doc2.fold_starting_at(1) is not None)
        doc2.unfold_all()
        t2.mark_set("insert", "3.10")
        app.expand_selection()
        check("expand selection to word", t2.get("sel.first", "sel.last") == "return")
        app.expand_selection()
        check("expand selection to line", t2.get("sel.first", "sel.last") == "        return 1",
              t2.get("sel.first", "sel.last"))
        app.shrink_selection()
        app.shrink_selection()
        t2.tag_remove("sel", "1.0", "end")
        t2.mark_set("insert", "5.4")
        app.step_number(1)
        check("increment number", doc2._line(5) == "x = 3")
        t2.mark_set("insert", "5.0")
        answers["string"].append("y")
        app.rename_symbol()
        check("rename symbol", doc2._line(5) == "y = 3")
        t2.mark_set("insert", "1.7")
        app.goto_definition("m")
        check("go to definition", t2.index("insert").startswith("2."))
        answers["string"].append("return|class")
        app.filter_view()
        pump()
        check("filter lines view", "filtered_out" in t2.tag_names("2.0")
              and "filtered_out" not in t2.tag_names("3.0"))
        app.clear_filter()
        check("lookup docs for builtins", "len" in (app.lookup_doc(doc2, "len") or ""))

        doc2.colsel = None
        t2.delete("1.0", "end")
        t2.insert("1.0", "aaa\nbbb\nccc")
        doc2.colsel = {"anchor": (1, 1), "cur": (3, 2), "view": t2}
        app._set_tag(t2, "NotepadColumn", True)
        app.column_draw(doc2)
        check("column selection text", app.column_text(doc2) == "a\nb\nc")
        app.column_key(types.SimpleNamespace(widget=t2, state=0, keysym="X", char="X"))
        check("column typing edits all lines", doc2.content() == "aXa\nbXb\ncXc", doc2.content())
        app.column_clear(doc2)

        doc3 = app.new_tab()
        t3 = doc3.text
        doc3.lang_override = "markup"
        doc3.setup_language()
        t3.insert("1.0", "ul>li.item$*2")
        t3.mark_set("insert", "end-1c")
        doc3._on_tab(ev(t3))
        check("emmet expansion", doc3.content() == '<ul>\n    <li class="item1"></li>\n'
                                                   '    <li class="item2"></li>\n</ul>',
              doc3.content())
        t3.delete("1.0", "end")
        t3.insert("1.0", "<div class='a'")
        t3.mark_set("insert", "end-1c")
        doc3._on_greater(ev(t3))
        check("html tag auto close", doc3.content() == "<div class='a'></div>")

        doc4 = app.new_tab()
        t4 = doc4.text
        doc4.lang_override = "markdown"
        doc4.setup_language()
        t4.insert("1.0", "# Title\n\n- one")
        t4.mark_set("insert", "end-1c")
        doc4._on_return(ev(t4))
        check("markdown list continues", doc4.content().endswith("- one\n- "))
        t4.insert("insert", "two **bold**")
        app.toggle_md_preview()
        pump()
        check("markdown preview pane", doc4.md_text is not None and "bold" in doc4.md_text.get(
            "1.0", "end") and doc4.md_text.tag_ranges("md_b"))
        app.toggle_md_preview()
        t4.mark_set("insert", "1.0")
        app.insert_toc()
        check("markdown table of contents", "- [Title](#title)" in doc4.content())

        doc5 = app.new_tab()
        t5 = doc5.text
        t5.insert("1.0", "b\na\nb\nc  \n")
        app.sort_lines()
        check("sort lines", doc5.content() == "\na\nb\nb\nc  ", doc5.content())
        app.unique_lines()
        app.trim_trailing()
        check("unique + trim", doc5.content() == "\na\nb\nc", doc5.content())
        app.reverse_lines()
        check("reverse lines", doc5.content() == "c\nb\na\n")
        t5.delete("1.0", "end")
        t5.insert("1.0", "helloWorld example")
        t5.tag_add("sel", "1.0", "1.end")
        app.convert_case_cmd("snake")
        check("snake_case", doc5.content() == "hello_world_example", doc5.content())
        app.convert_case_cmd("camel")
        check("camelCase", doc5.content() == "helloWorldExample", doc5.content())
        t5.delete("1.0", "end")
        t5.insert("1.0", "a\u200bb\u00a0c \u201cq\u201d")
        app.clean_invisible_cmd()
        app.straighten_quotes_cmd()
        check("clean invisible + quotes", doc5.content() == 'ab c "q"', doc5.content())
        t5.delete("1.0", "end")
        t5.insert("1.0", '{"b":1,"a":[1,2]}')
        app.sort_json_keys()
        check("sort json keys", doc5.content().startswith('{\n    "a"'))
        t5.delete("1.0", "end")
        t5.insert("1.0", "<a><b/></a>")
        app.format_xml()
        check("format xml", doc5.content() == "<a>\n    <b/>\n</a>", doc5.content())
        t5.delete("1.0", "end")
        t5.insert("1.0", "x = 1\nlong_name = 2")
        answers["string"].append("=")
        t5.tag_add("sel", "1.0", "end-1c")
        app.align_columns()
        check("align columns", doc5.content() == "x         = 1\nlong_name = 2", doc5.content())
        t5.delete("1.0", "end")
        t5.insert("1.0", "255")
        t5.mark_set("insert", "1.1")
        app.convert_number("hex")
        check("number to hex", doc5.content() == "0xff")
        t5.delete("1.0", "end")
        t5.insert("1.0", "2+3*4 =")
        t5.mark_set("insert", "1.end")
        app.calculate()
        check("calculator", doc5.content() == "2+3*4 = 14")
        t5.delete("1.0", "end")
        t5.insert("1.0", "<b>&")
        t5.tag_add("sel", "1.0", "end-1c")
        app.escape_tool("html_e")
        check("escape html", doc5.content() == "&lt;b&gt;&amp;")

        bad = write("bad.json", '{\n  "a": 1,\n  "b": \n}')
        docj = app.open_file(bad)
        app.validate_cmd()
        check("validate json marks error", docj.syntax_error and docj.syntax_error[0] in (3, 4))
        pyerr = write("err.py", "def f(:\n    pass\n")
        docp = app.open_file(pyerr)
        app.check_syntax(docp, quiet=True)
        check("python syntax check", docp.syntax_error and docp.syntax_error[0] == 1)

        csvp = write("data.csv", "name,age\nAna,30\nLuis,25\n")
        app.open_file(csvp)
        before = len(root.winfo_children())
        app.csv_table()
        check("csv table view", len(root.winfo_children()) > before)
        jsp = write("data.json", '{"a": {"b": [1, 2]}}')
        app.open_file(jsp)
        before = len(root.winfo_children())
        app.json_tree()
        check("json tree view", len(root.winfo_children()) > before)

        png = os.path.join(work, "img.png")
        img = tk.PhotoImage(width=8, height=6)
        img.put("#FF0000", to=(0, 0, 8, 6))
        img.write(png, format="png")
        dimg = app.open_file(png)
        check("image viewer", dimg and dimg.kind == "image" and dimg.image_source.width() == 8)
        app.zoom(1)
        check("image zoom", dimg.image_scale == 2)

        binp = write("blob.bin", bytes(range(256)) * 4)
        answers["yesno"].append(True)
        dhex = app.open_file(binp)
        check("hex viewer", dhex and dhex.kind == "hex" and dhex.content().startswith(
            "00000000  00 01 02"))

        zpath = os.path.join(work, "arch.zip")
        with zipfile.ZipFile(zpath, "w") as z:
            z.writestr("folder/readme.md", "# Inside zip")
        before = len(root.winfo_children())
        app.open_archive(zpath)
        check("archive explorer", len(root.winfo_children()) > before)

        log = write("app.log", "2026-01-01 10:00:00 INFO start\n")
        dlog = app.open_file(log)
        check("log highlighting", dlog.lang == "log")
        app.toggle_follow()
        with open(log, "a", encoding="utf-8") as f:
            f.write("2026-01-01 10:00:01 ERROR boom\n")
        for _ in range(150):
            pump(1)
            if "boom" in dlog.content():
                break
        check("follow file (tail)", "boom" in dlog.content())
        app.toggle_follow()

        big = write("big.txt", "line\n" * 10)
        old_large = globals()["LARGE_FILE"]
        globals()["LARGE_FILE"] = 10
        answers["yesno"].append(True)
        dlarge = app.open_file(big)
        globals()["LARGE_FILE"] = old_large
        check("large file viewer", dlarge and dlarge.kind == "large" and dlarge.read_only)

        sp = app.open_scratchpad()
        sp.text.insert("1.0", "note")
        sp.refresh()
        with open(SCRATCH_FILE, encoding="utf-8") as f:
            check("scratchpad autosaves", f.read() == "note")

        docs_before = len(app.docs)
        app.new_tab()
        dtpl = app.current()
        dtpl.text.insert("1.0", TEMPLATES["Python Script"][1])
        check("templates available", len(TEMPLATES) >= 8 and len(app.docs) == docs_before + 1)

        saved = write("hist.txt", "v1")
        dh = app.open_file(saved)
        dh.text.insert("end", " v2")
        app.save(dh)
        dh.text.insert("end", " v3")
        app.save(dh)
        check("local history versions", len(app.history_versions(saved)) >= 2)
        dh.snapshot_test = True
        dh._snapshot()
        dh.text.insert("end", " v4")
        dh._snapshot()
        app.save_undo_history(dh)
        dh.undo_prev = []
        app.load_undo_history(dh)
        check("persistent undo history", len(dh.undo_prev) >= 1)
        app.backup_bak.set(True)
        app.save(dh)
        app.backup_bak.set(False)
        check(".bak backup on save", os.path.exists(saved + ".bak"))

        pdf = build_pdf("hello (world)\n" * 100, "test.txt")
        check("pdf export", pdf.startswith(b"%PDF-1.4") and pdf.rstrip().endswith(b"%%EOF")
              and b"/Count 2" in pdf)
        page = export_html("x = 1", "python", app.theme, "t", True)
        check("html export", "<pre" in page and "span" in page)
        check("emmet parser", emmet_expand("a", "  ")[0] == '<a href=""></a>')
        check("test data", generate_test_data(3, "CSV").count("\n") == 3)
        check("seq to accel", seq_to_accel("<Control-Shift-S>") == "Ctrl+Shift+S")
        check("indent detection", detect_indentation("a:\n  b\n  c\n    d\n  e\n") == (True, 2))

        before = len(opened_urls)
        mdp = write("readme.md", "# Hi\n\n[link](other.md)\n")
        dmd = app.open_file(mdp)
        app.preview()
        check("markdown preview server", len(opened_urls) > before
              and opened_urls[-1].startswith("http://127.0.0.1"))
        if opened_urls and opened_urls[-1].startswith("http://127.0.0.1"):
            with urllib.request.urlopen(opened_urls[-1], timeout=5) as resp:
                check("preview serves content", b"<h1>Hi</h1>" in resp.read())
        check("ctrl+click opens relative files", app.open_link("readme.md", dmd))

        class Handler(http.server.BaseHTTPRequestHandler):
            def do_POST(self):
                body = self.rfile.read(int(self.headers.get("Content-Length", 0)))
                data = json.dumps({"got": json.loads(body)}).encode()
                self.send_response(201)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

            def log_message(self, *args):
                pass

        server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        httpf = write("api.http", f"@host = http://127.0.0.1:{server.server_address[1]}\n\n"
                                  "### create\nPOST {{host}}/items\nContent-Type: application/json"
                                  '\n\n{"name": "x"}\n')
        dhttp = app.open_file(httpf)
        dhttp.text.mark_set("insert", "5.0")
        app.run_file()
        response = None
        for _ in range(300):
            pump(1)
            cur = app.current()
            if cur is not dhttp and cur.display_name and cur.display_name.startswith("Response"):
                response = cur
                break
        check("http client", response is not None and '"got"' in response.content()
              and "201" in response.display_name)
        server.shutdown()

        sqlf = write("q.sql", "CREATE TABLE t (n INTEGER);\nINSERT INTO t VALUES (1), (2);\n"
                              "SELECT SUM(n) AS total FROM t;\n")
        app.open_file(sqlf)
        answers["save"].append(os.path.join(work, "test.db"))
        app.run_file()
        out = app.out_text.get("1.0", "end")
        check("sqlite runner", "OK" in out and "1 row(s)" in out, out)

        runner = write("run_me.py", "print('hello from python')\nraise SystemExit(3)\n")
        app.open_file(runner)
        app.run_file()
        for _ in range(400):
            pump(1)
            if app.proc is None:
                break
        out = app.out_text.get("1.0", "end")
        check("run file output", "hello from python" in out and "exit code 3" in out, out)

        app.show_console()
        app.console_text.insert("end", "1 + 41")
        app._console_enter()
        check("python console", "42" in app.console_text.get("1.0", "end"))
        app.hide_output()

        app.explorer_var.set(True)
        app.set_explorer_root(work)
        pump()
        names = [app.explorer.item(n, "text").strip() for n in app.explorer.get_children()]
        check("explorer lists files", "a.py" in names and names[0] == "..", names)
        check("explorer file icons", app.explorer.item(app.explorer.get_children()[1], "image"))
        app._explorer_click(types.SimpleNamespace(y=app.explorer.bbox(
            app.explorer.get_children()[0])[1] + 2, x=40))
        check("explorer .. goes up", os.path.normcase(app.explorer_root) ==
              os.path.normcase(os.path.dirname(work)))
        app.set_explorer_root(work)
        answers["string"].append("made.txt")
        app.explorer_new(folder=False, base=work)
        check("explorer new file", os.path.exists(os.path.join(work, "made.txt"))
              and app.current().path.endswith("made.txt"))
        app.set_side_view(None)
        check("side bar close button", not app.side_visible)
        app.activity_explorer()
        check("activity bar opens explorer", app.side_visible and app.side_view() == "explorer")
        app.open_file(py)
        app.set_side_view("outline")
        pump()
        check("outline panel", len(app.outline.get_children()) >= 1)
        app.explorer_var.set(False)
        app.outline_var.set(False)
        app.update_side_panel()

        cur = app.open_file(py)
        app.toggle_split()
        pump()
        check("split view", cur.peer is not None)
        app.toggle_split()
        app.show_minimap.set(True)
        app.toggle_minimap()
        pump(20)
        cur.redraw_minimap()
        check("minimap", len(cur.minimap.find_all()) > 1)
        app.show_minimap.set(False)
        app.toggle_minimap()

        for var in (app.show_ws, app.show_guides, app.mark_long, app.show_ruler):
            var.set(True)
        app.ruler_col.set(10)
        cur.text.insert("end", "\n        very_long_line_here = 1")
        app.refresh_decorations()
        pump()
        check("indent guides", cur.text.tag_ranges("guide"))
        check("show whitespace", cur.text.tag_ranges("ws_space"))
        check("mark long lines", cur.text.tag_ranges("longline"))
        check("ruler", cur.ruler.winfo_ismapped())
        for var in (app.show_ws, app.mark_long, app.show_ruler):
            var.set(False)
        app.ruler_col.set(80)
        app.refresh_decorations()
        cur.text.insert("end", "\nx = ((1))")
        cur.refresh()
        check("rainbow brackets", cur.text.tag_ranges("rb0") and cur.text.tag_ranges("rb1"))

        app.focus_mode.set(True)
        cur._cursor_idle()
        check("focus mode dims", cur.text.tag_ranges("dim"))
        app.focus_mode.set(False)
        cur._cursor_idle()

        app.vim_var.set(True)
        app.toggle_vim()
        vd = app.new_tab()
        vt = vd.text
        vt.insert("1.0", "one\ntwo\nthree")
        vt.mark_set("insert", "1.0")
        for key in ("j", "d", "d"):
            app.vim_key(types.SimpleNamespace(widget=vt, state=0, keysym=key, char=key))
        check("vim dd deletes line", vd.content() == "one\nthree", vd.content())
        app.vim_key(types.SimpleNamespace(widget=vt, state=0, keysym="i", char="i"))
        check("vim insert mode", vd.vim_mode == "insert")
        app.vim_var.set(False)
        app.toggle_vim()

        md = app.new_tab()
        mt = md.text
        mt.focus_force()
        pump()
        app.toggle_macro_recording()
        for key in ("a", "b"):
            app._macro_capture(types.SimpleNamespace(keysym=key, state=0, char=key))
        app.toggle_macro_recording()
        app.play_macro()
        pump()
        check("macro playback", md.content() == "ab", md.content())

        mt.insert("1.0", "copy me ")
        mt.tag_add("sel", "1.0", "1.4")
        root.clipboard_clear()
        root.clipboard_append("copy")
        app._record_clipboard()
        check("clipboard history", app.clip_history and app.clip_history[0] == "copy")

        app.toggle_pin(md)
        check("pin tab", md.pinned and not app.close_tab(md))
        app.toggle_pin(md)
        app.set_tab_color(md, "#E05252")
        check("tab color", app.nb.tab(md.frame, "image") not in ("", ()))

        app.ui_scale.set("150")
        app.apply_ui_scale()
        app.ui_scale.set("100")
        app.apply_ui_scale()
        check("interface scale", True)
        app.theme_var.set("High Contrast")
        app.set_theme()
        check("high contrast theme", app.theme["bg"] == "#000000")
        app.theme_var.set("Blue")
        app.set_theme()

        app.lang_var.set("sql")
        app.set_language_mode()
        check("language mode override", md.lang == "sql")

        app.pomodoro = None
        app.toggle_pomodoro()
        check("pomodoro", "Focus" in app.status_items["pomodoro"].cget("text"))
        app.toggle_pomodoro()

        check("command palette has commands", len(app.palette_items) > 150)
        app.command_palette()
        pump()
        app.palette_win.destroy()
        app.palette_win = None
        app.shortcuts_window()
        app.settings_window()
        pump()
        check("help and settings windows", True)

        kb = load_json_file(KEYBINDINGS_FILE, None)
        app.edit_keybindings()
        bindings = load_json_file(KEYBINDINGS_FILE, {})
        bindings["edit.join"] = ["<Control-Shift-J>"]
        bindings["view.outline"] = []
        kdoc = app.current()
        kdoc.text.delete("1.0", "end")
        kdoc.text.insert("1.0", json.dumps(bindings, indent=2))
        app.save(kdoc)
        check("custom keybindings", app.accel("edit.join") == "Ctrl+Shift+J" and kb is None)

        app.report_error(ValueError, ValueError("test error"), None)
        with open(ERROR_LOG, encoding="utf-8") as f:
            check("error log", "test error" in f.read())

        if shutil.which("git"):
            repo = os.path.join(work, "repo")
            os.makedirs(repo)
            target = os.path.join(repo, "g.txt")
            with open(target, "w", encoding="utf-8") as f:
                f.write("a\nb\n")
            for cmd in (["init", "-q"], ["add", "g.txt"],
                        ["-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "x"]):
                subprocess.run(["git"] + cmd, cwd=repo, capture_output=True)
            dg = app.open_file(target)
            dg.text.insert("1.0", "new\n")
            dg.refresh()
            check("git branch and changed lines", dg.git_branch and dg.git_marks.get(1) == "add",
                  (dg.git_branch, dg.git_marks))

        payload_file = write("sent.txt", "sent")
        app.instance_serve()
        ok = Notepad.instance_connect({"files": [payload_file], "cwd": work})
        for _ in range(50):
            pump(1)
            if app._find_open(payload_file):
                break
        check("single instance forwarding", ok and app._find_open(payload_file))
        app.instance_stop()

        session_count = len([d for d in app.ordered_docs() if d.path and d.kind == "text"])
        for d in app.ordered_docs():
            d.text.edit_modified(False)
        app.exit()
        root2 = tk.Tk()
        app2 = Notepad(root2)
        app2.start([])
        for _ in range(10):
            root2.update()
        restored = len([d for d in app2.ordered_docs() if d.path and d.kind == "text"])
        check("session restore", restored >= session_count - 1, (restored, session_count))
        for d in app2.ordered_docs():
            d.text.edit_modified(False)
            d.pinned = False
        app2.exit()
    except Exception:
        traceback.print_exc()
        results.append(("unexpected exception", False))
        try:
            root.destroy()
        except tk.TclError:
            pass
    finally:
        shutil.rmtree(work, ignore_errors=True)
    failed = [name for name, ok in results if not ok]
    print(f"\n{len(results) - len(failed)}/{len(results)} checks passed")
    if failed:
        print("Failed: " + ", ".join(failed))
    return 1 if failed else 0


def main():
    parser = argparse.ArgumentParser(
        prog="notepad.py",
        description="A cross-platform text and code editor that only needs Python.")
    parser.add_argument("files", nargs="*",
                        help="files to open; use file:line to jump to a line and - to read "
                             "standard input")
    parser.add_argument("--new-window", action="store_true",
                        help="open a new window instead of using the running one")
    parser.add_argument("--selftest", action="store_true",
                        help="run the built-in tests and exit")
    args, _ = parser.parse_known_args()
    if args.selftest:
        sys.exit(run_self_test())
    stdin_text = None
    files = [f for f in args.files if f != "-"]
    if "-" in args.files and sys.stdin is not None:
        try:
            stdin_text = decode_bytes(sys.stdin.buffer.read())[0]
        except (OSError, AttributeError, ValueError):
            stdin_text = None
    cfg = load_config()
    if not args.new_window and cfg.get("single_instance", True):
        if Notepad.instance_connect({"files": files, "stdin": stdin_text, "cwd": os.getcwd()}):
            return
    if sys.platform == "win32":
        try:
            from ctypes import windll
            windll.shcore.SetProcessDpiAwareness(1)
        except (ImportError, AttributeError, OSError):
            pass
    root = tk.Tk()
    app = Notepad(root)
    app.start(files, stdin_text)
    root.mainloop()


if globals().get("__name__", "__main__") == "__main__":
    main()
