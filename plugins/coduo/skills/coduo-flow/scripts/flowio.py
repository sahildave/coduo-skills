"""Encoding-safe file IO and the shared note scan.

Every note is read and every artifact written as UTF-8 explicitly. Relying on
the platform default breaks the moment a note contains an em dash and the
process runs under a C locale — and worse, `UnicodeDecodeError` subclasses
`ValueError`, so the failure used to surface as "no frontmatter block", which
is a wholly false diagnosis.

The note scan lives here rather than in both scripts, so adding a frontmatter
field is one edit and the checker cannot drift from what the builder reads.
"""

import os

import frontmatter


def read_text(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def write_text(path, text):
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def read_json(path):
    import json
    return json.loads(read_text(path))


def note_files(flow_dir, index):
    """Every markdown file in the folder that is a note, in filename order —
    which is also the reading order the panel steps through.

    `index` is one filename or a list of them: the folder's own README, and any
    companion prose that lives beside the notes without being one."""
    skip = {index} if isinstance(index, str) else set(index or ())
    return [n for n in sorted(os.listdir(flow_dir))
            if n.endswith(".md") and n not in skip]


def read_note(flow_dir, name):
    """-> (frontmatter dict, body). Raises ValueError only for a genuinely
    missing frontmatter block; a decode problem raises UnicodeDecodeError."""
    return frontmatter.split(read_text(os.path.join(flow_dir, name)))
