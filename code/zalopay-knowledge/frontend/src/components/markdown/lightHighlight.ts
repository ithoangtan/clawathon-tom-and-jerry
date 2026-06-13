/** Lightweight syntax highlighter — zero deps, good enough for chat code fences. */

const KEYWORDS: Record<string, Set<string>> = {
  javascript: new Set([
    "const", "let", "var", "function", "return", "if", "else", "for", "while",
    "class", "extends", "import", "export", "from", "default", "async", "await",
    "try", "catch", "throw", "new", "typeof", "instanceof", "null", "undefined",
    "true", "false", "this", "switch", "case", "break", "continue",
  ]),
  typescript: new Set([
    "const", "let", "var", "function", "return", "if", "else", "for", "while",
    "class", "extends", "import", "export", "from", "default", "async", "await",
    "interface", "type", "enum", "implements", "public", "private", "protected",
    "readonly", "as", "keyof", "typeof", "null", "undefined", "true", "false",
  ]),
  python: new Set([
    "def", "class", "return", "if", "elif", "else", "for", "while", "import",
    "from", "as", "with", "try", "except", "finally", "raise", "pass", "break",
    "continue", "lambda", "yield", "async", "await", "True", "False", "None",
    "and", "or", "not", "in", "is",
  ]),
  bash: new Set([
    "if", "then", "else", "elif", "fi", "for", "do", "done", "while", "case",
    "esac", "function", "return", "export", "local", "echo", "exit",
  ]),
  sql: new Set([
    "SELECT", "FROM", "WHERE", "INSERT", "INTO", "VALUES", "UPDATE", "SET",
    "DELETE", "JOIN", "LEFT", "RIGHT", "INNER", "OUTER", "ON", "AND", "OR",
    "NOT", "NULL", "AS", "ORDER", "BY", "GROUP", "HAVING", "LIMIT", "OFFSET",
    "CREATE", "TABLE", "INDEX", "DROP", "ALTER", "PRIMARY", "KEY", "FOREIGN",
    "REFERENCES", "DISTINCT", "COUNT", "SUM", "AVG", "MAX", "MIN",
  ]),
  json: new Set(),
};

function escapeHtml(text: string): string {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

function span(cls: string, text: string): string {
  return `<span class="${cls}">${escapeHtml(text)}</span>`;
}

function highlightLine(line: string, lang: string): string {
  const keywords = KEYWORDS[lang] ?? KEYWORDS.javascript;

  if (lang === "json") {
    return line.replace(
      /("(?:\\.|[^"\\])*")\s*(:)?|\b(true|false|null)\b|-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?/g,
      (match, str, colon, bool) => {
        if (str) return colon ? `${span("hl-key", str)}${colon}` : span("hl-string", str);
        if (bool) return span("hl-keyword", bool);
        return span("hl-number", match);
      },
    );
  }

  // Comments
  if (lang === "python" || lang === "bash" || lang === "sql") {
    const hashIdx = line.indexOf("#");
  if (hashIdx >= 0 && lang !== "sql") {
      return (
        highlightLine(line.slice(0, hashIdx), lang) +
        span("hl-comment", line.slice(hashIdx))
      );
    }
    if (lang === "sql" && line.trimStart().startsWith("--")) {
      return span("hl-comment", line);
    }
  }

  const slashComment = line.match(/^(\s*)(\/\/.*)$/);
  if (slashComment && (lang === "javascript" || lang === "typescript")) {
    return highlightLine(slashComment[1], lang) + span("hl-comment", slashComment[2]);
  }

  // Tokenize with regex for strings, numbers, identifiers
  return line.replace(
    /("(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*'|`(?:\\.|[^`\\])*`)|\b(-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)\b|([a-zA-Z_$][\w$]*)/g,
    (match, str, num, ident) => {
      if (str) return span("hl-string", str);
      if (num) return span("hl-number", num);
      if (ident) {
        const lower = lang === "sql" ? ident.toUpperCase() : ident;
        if (keywords.has(lower) || keywords.has(ident)) return span("hl-keyword", ident);
        if (ident[0] === ident[0].toUpperCase() && ident[0] !== ident[0].toLowerCase()) {
          return span("hl-type", ident);
        }
        return span("hl-ident", ident);
      }
      return escapeHtml(match);
    },
  );
}

export function highlightCode(code: string, language: string): string {
  const lang = normalizeLanguage(language);
  return code
    .split("\n")
    .map((line) => highlightLine(line, lang))
    .join("\n");
}

export function normalizeLanguage(lang: string): string {
  const l = lang.toLowerCase().trim();
  const aliases: Record<string, string> = {
    js: "javascript",
    ts: "typescript",
    py: "python",
    sh: "bash",
    shell: "bash",
    zsh: "bash",
    yml: "yaml",
    md: "markdown",
    plaintext: "text",
    text: "text",
  };
  return aliases[l] ?? l;
}

export function displayLanguage(lang: string): string {
  const normalized = normalizeLanguage(lang);
  const labels: Record<string, string> = {
    javascript: "JavaScript",
    typescript: "TypeScript",
    python: "Python",
    bash: "Bash",
    sql: "SQL",
    json: "JSON",
    yaml: "YAML",
    markdown: "Markdown",
    text: "Plain text",
  };
  return labels[normalized] ?? lang.charAt(0).toUpperCase() + lang.slice(1);
}
