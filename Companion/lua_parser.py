"""Minimal parser for World of Warcraft SavedVariables files (Lua table constructors)."""

import re

_NUMBER = re.compile(r"-?(?:0[xX][0-9a-fA-F]+|\d+\.?\d*(?:[eE][+-]?\d+)?|\.\d+)")
_NAME = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
_ESCAPES = {"n": "\n", "t": "\t", "r": "\r", "\\": "\\", '"': '"', "'": "'"}


class LuaParseError(ValueError):
    pass


class _Parser:
    def __init__(self, text):
        self.s = text
        self.i = 0

    def error(self, message):
        line = self.s.count("\n", 0, self.i) + 1
        raise LuaParseError(f"{message} (line {line})")

    def skip(self):
        s = self.s
        while self.i < len(s):
            if s[self.i].isspace():
                self.i += 1
            elif s.startswith("--", self.i):
                end = s.find("\n", self.i)
                self.i = len(s) if end == -1 else end + 1
            else:
                break

    def expect(self, char):
        self.skip()
        if self.i >= len(self.s) or self.s[self.i] != char:
            self.error(f"Expected '{char}'")
        self.i += 1

    def string(self):
        quote = self.s[self.i]
        self.i += 1
        out = []
        while self.i < len(self.s):
            c = self.s[self.i]
            if c == quote:
                self.i += 1
                return "".join(out)
            if c == "\\":
                self.i += 1
                n = self.s[self.i]
                if n.isdigit():
                    digits = re.match(r"\d{1,3}", self.s[self.i:]).group()
                    out.append(chr(int(digits)))
                    self.i += len(digits)
                    continue
                out.append(_ESCAPES.get(n, n))
            else:
                out.append(c)
            self.i += 1
        self.error("Unterminated string")

    def value(self):
        self.skip()
        s = self.s
        c = s[self.i] if self.i < len(s) else ""
        if c == "{":
            return self.table()
        if c in ("\"", "'"):
            return self.string()
        m = _NUMBER.match(s, self.i)
        if m:
            self.i = m.end()
            text = m.group()
            if text.lower().lstrip("-").startswith("0x"):
                return int(text, 16)
            return float(text) if re.search(r"[.eE]", text) else int(text)
        m = _NAME.match(s, self.i)
        if m:
            self.i = m.end()
            return {"true": True, "false": False, "nil": None}.get(m.group(), m.group())
        self.error("Unexpected token")

    def table(self):
        self.i += 1
        items = []  # (key, value); key None means positional
        while True:
            self.skip()
            if self.i >= len(self.s):
                self.error("Unterminated table")
            c = self.s[self.i]
            if c == "}":
                self.i += 1
                break
            if c in ",;":
                self.i += 1
                continue
            key = None
            if c == "[":
                self.i += 1
                key = self.value()
                self.expect("]")
                self.expect("=")
            else:
                m = _NAME.match(self.s, self.i)
                if m:
                    j = m.end()
                    while j < len(self.s) and self.s[j].isspace():
                        j += 1
                    if self.s[j : j + 1] == "=" and self.s[j + 1 : j + 2] != "=":
                        key = m.group()
                        self.i = j + 1
            items.append((key, self.value()))

        if items and all(k is None for k, _ in items):
            return [v for _, v in items]
        result = {}
        position = 1
        for key, val in items:
            if key is None:
                key = position
                position += 1
            result[key] = val
        return result


def parse_saved_variables(text):
    """Return {variable_name: value} for each top-level `Name = <value>` assignment."""
    parser = _Parser(text)
    result = {}
    while True:
        parser.skip()
        if parser.i >= len(parser.s):
            return result
        m = _NAME.match(parser.s, parser.i)
        if not m:
            parser.error("Expected variable name")
        parser.i = m.end()
        parser.expect("=")
        result[m.group()] = parser.value()


def load_saved_variables(path):
    with open(path, "r", encoding="utf-8", errors="replace") as handle:
        return parse_saved_variables(handle.read())
