#!/usr/bin/env python3
"""Test suite for coduo-flow. Stdlib unittest, no dependencies.

    python3 tests/test_flow.py

Covers the two script-level contracts (markdown subset, frontmatter shapes),
the checker's failure modes, and the two behaviours the eval found broken:
cross-note links, and flows that loop back.
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(SKILL, "scripts"))

import flowmd
import frontmatter

CHECK = os.path.join(SKILL, "scripts", "check_flow.py")
BUILD = os.path.join(SKILL, "scripts", "build_flow.py")
SHELL = os.path.join(SKILL, "assets", "flow-shell.html")


def note(nid, node, kind="finding", dep=(), unl=(), extra="", body="# T\n\n## A section\n\nText.\n"):
    return (
        "---\nid: %s\ntitle: Title for %s\nnode: %s\nkind: %s\nstatus: proposed\n"
        "confidence: high\nsummary: A one sentence answer.\n"
        "depends_on: [%s]\nunlocks: [%s]\nupdated: 2026-08-22\n%s---\n\n%s"
        % (nid, nid, node, kind, ", ".join(dep), ", ".join(unl), extra, body)
    )


class Flow(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.dir)

    def write(self, name, text):
        with open(os.path.join(self.dir, name), "w") as f:
            f.write(text)

    def config(self, **kw):
        cfg = {"title": "T", "out": "flow.html"}
        cfg.update(kw)
        self.write("flow.json", json.dumps(cfg))

    def check(self):
        return subprocess.run([sys.executable, CHECK, self.dir], capture_output=True, text=True)

    def build(self):
        return subprocess.run([sys.executable, BUILD, self.dir], capture_output=True, text=True)

    def html(self):
        with open(os.path.join(self.dir, "flow.html")) as f:
            return f.read()

    def minimal(self):
        """Two notes, one edge — the smallest valid flow."""
        self.config()
        self.write("01-a.md", note("a", "A", unl=["b"]))
        self.write("02-b.md", note("b", "B", dep=["a"]))


# ------------------------------------------------- risks and questions
class TestOpenItems(Flow):
    """A risk and an open question are one frontmatter line each, split on the
    first colon like `facts`. The prefix is read only when it is entirely
    tokens we know — otherwise the whole sentence survives."""

    def test_severity_and_mitigation_are_read_from_the_prefix(self):
        import build_flow
        r = build_flow.parse_risk("high, mitigated: The cutover needs a second night.")
        self.assertEqual((r["sev"], r["mitigated"]), ("high", True))
        self.assertEqual(r["text"], "The cutover needs a second night.")

    def test_a_risk_with_no_prefix_keeps_its_whole_sentence(self):
        import build_flow
        r = build_flow.parse_risk("Postgres 17: the upgrade window slips a week.")
        self.assertEqual(r["text"], "Postgres 17: the upgrade window slips a week.")
        self.assertEqual((r["sev"], r["mitigated"]), ("medium", False))

    def test_question_prefix_is_a_deadline_and_answered_is_reserved(self):
        import build_flow
        q = build_flow.parse_question("week 1: Who owns the contract?")
        self.assertEqual((q["when"], q["answered"]), ("week 1", False))
        self.assertTrue(build_flow.parse_question("answered: Yes, in July.")["answered"])

    def test_a_long_head_is_the_question_not_a_deadline(self):
        import build_flow
        q = build_flow.parse_question("Who signs off the evidence pack: security or legal?")
        self.assertEqual(q["when"], "")
        self.assertIn("evidence pack", q["text"])

    def test_sections_render_and_link_back_to_their_note(self):
        self.config()
        self.write("01-a.md", note("a", "A", unl=["b"], extra=(
            "risks:\n  - \"high: The lag window is untested.\"\n"
            "questions:\n  - \"week 1: Can the move run during the upgrade?\"\n")))
        self.write("02-b.md", note("b", "B", dep=["a"], extra=(
            "risks:\n  - \"low, mitigated: A late freeze forces rework.\"\n")))
        self.assertEqual(self.build().returncode, 0)
        html = self.html()
        self.assertIn('id="tab-risks"', html)
        self.assertIn('id="tab-questions"', html)
        self.assertIn("The lag window is untested.", html)
        # every row names the note it came from, and that link opens the panel
        self.assertIn('<button type="button" data-note="a">A</button>', html)
        self.assertIn('class="rows settled"', html)   # the mitigated one

    def test_quick_view_counts_what_is_still_open(self):
        self.config()
        self.write("01-a.md", note("a", "A", unl=["b"], extra=(
            "risks:\n  - \"high: Unheld.\"\n  - \"low, mitigated: Held.\"\n"
            "questions:\n  - \"week 1: Open one?\"\n  - \"answered: Shut one? Yes.\"\n")))
        self.write("02-b.md", note("b", "B", dep=["a"]))
        self.assertEqual(self.build().returncode, 0)
        html = self.html()
        self.assertIn('<b class="hot">1</b>', html)          # 1 unmitigated risk
        self.assertIn("unmitigated risk<", html)             # singular
        self.assertIn("of 2 tracked", html)
        self.assertIn("1 answered", html)

    def test_no_open_items_means_no_quick_view_and_no_tabs(self):
        self.minimal()
        self.assertEqual(self.build().returncode, 0)
        html = self.html()
        self.assertNotIn('class="quick"', html)
        self.assertNotIn('role="tablist"', html)
        self.assertNotIn("{{", html)

    def test_tab_bar_appears_once_there_is_a_second_panel(self):
        self.config()
        self.write("01-a.md", note("a", "A", unl=["b"], extra=(
            "questions:\n  - \"week 1: Anything?\"\n")))
        self.write("02-b.md", note("b", "B", dep=["a"]))
        self.assertEqual(self.build().returncode, 0)
        html = self.html()
        self.assertIn('role="tablist"', html)
        self.assertIn('data-tab="questions"', html)
        self.assertNotIn('data-tab="risks"', html)
        # the map is the first tab and stays visible with no script
        self.assertIn('<section class="tabpanel" id="tab-roadmap"', html)
        self.assertIn('id="tab-questions" role="tabpanel" aria-labelledby="tb-questions" hidden', html)

    def test_a_scalar_where_a_list_belongs_is_an_error(self):
        self.minimal()
        self.write("01-a.md", note("a", "A", unl=["b"], extra="risks: just one\n"))
        r = self.check()
        self.assertEqual(r.returncode, 1)
        self.assertIn("must be a list", r.stderr)

    def test_a_risk_with_no_severity_warns(self):
        self.minimal()
        self.write("01-a.md", note("a", "A", unl=["b"], extra=(
            "risks:\n  - \"Something might go wrong.\"\n")))
        r = self.check()
        self.assertEqual(r.returncode, 0)
        self.assertIn("names no severity", r.stderr)

    def test_a_question_without_a_question_mark_warns(self):
        self.minimal()
        self.write("01-a.md", note("a", "A", unl=["b"], extra=(
            "questions:\n  - \"week 1: Decide the owner.\"\n")))
        r = self.check()
        self.assertEqual(r.returncode, 0)
        self.assertIn("not phrased as a question", r.stderr)


# --------------------------------------------------------------- markdown
class TestMarkdown(unittest.TestCase):
    def test_table_with_pipe_inside_code_span(self):
        out, _ = flowmd.render("| a | b |\n| --- | --- |\n| `x|y` | 1 |")
        self.assertIn("<td><code>x|y</code></td>", out)
        self.assertEqual(out.count("<td>"), 2)

    def test_sections_are_h2_only(self):
        _, secs = flowmd.render("# One\n\n## Two\n\n### Three\n\n## Four\n")
        self.assertEqual([s[1] for s in secs], ["Two", "Four"])

    def test_nested_list(self):
        out, _ = flowmd.render("- one\n- two\n  - deep\n")
        self.assertIn("<li>two<ul><li>deep</li></ul></li>", out)

    def test_html_is_escaped(self):
        out, _ = flowmd.render("<script>alert(1)</script>")
        self.assertNotIn("<script>", out)

    def test_balanced_blocks(self):
        out, _ = flowmd.render("> quote\n\n```py\nx=1\n```\n\n| a |\n| --- |\n| 1 |\n")
        for tag in ("blockquote", "pre", "table"):
            self.assertEqual(out.count("<" + tag), out.count("</" + tag + ">"), tag)


# ------------------------------------------------------------ frontmatter
class TestFrontmatter(unittest.TestCase):
    def test_inline_array(self):
        fm = frontmatter.parse("depends_on: [a, b]")
        self.assertEqual(fm["depends_on"], ["a", "b"])

    def test_array_wrapped_by_a_formatter(self):
        """Prettier wraps long arrays; unwrapped this silently read as empty."""
        fm = frontmatter.parse("depends_on:\n  [alpha, beta, gamma]")
        self.assertEqual(fm["depends_on"], ["alpha", "beta", "gamma"])

    def test_array_wrapped_one_per_line(self):
        fm = frontmatter.parse("unlocks:\n  [\n    alpha,\n    beta,\n  ]")
        self.assertEqual(fm["unlocks"], ["alpha", "beta"])

    def test_block_list(self):
        fm = frontmatter.parse('facts:\n  - "Price: $7"\n  - "Cap: 250"')
        self.assertEqual(fm["facts"], ["Price: $7", "Cap: 250"])

    def test_wrapped_scalar(self):
        fm = frontmatter.parse("summary: One sentence that\n  wrapped onto two lines.")
        self.assertEqual(fm["summary"], "One sentence that wrapped onto two lines.")


# ---------------------------------------------------------------- checker
class TestChecker(Flow):
    def test_valid_flow_passes(self):
        self.minimal()
        self.assertEqual(self.check().returncode, 0)

    def test_dangling_dependency(self):
        self.config()
        self.write("01-a.md", note("a", "A", dep=["ghost"]))
        r = self.check()
        self.assertEqual(r.returncode, 1)
        self.assertIn('"ghost" does not exist', r.stderr)

    def test_one_way_edge(self):
        self.config()
        self.write("01-a.md", note("a", "A"))                 # no unlocks
        self.write("02-b.md", note("b", "B", dep=["a"]))
        r = self.check()
        self.assertEqual(r.returncode, 1)
        self.assertIn("unlocks is missing", r.stderr)

    def test_dependency_cycle(self):
        self.config()
        self.write("01-a.md", note("a", "A", dep=["b"], unl=["b"]))
        self.write("02-b.md", note("b", "B", dep=["a"], unl=["a"]))
        r = self.check()
        self.assertEqual(r.returncode, 1)
        self.assertIn("cycle", r.stderr)

    def test_kind_outside_vocabulary(self):
        self.config()
        self.write("01-a.md", note("a", "A", kind="insight"))
        r = self.check()
        self.assertEqual(r.returncode, 1)
        self.assertIn("insight", r.stderr)

    def test_node_label_too_long(self):
        self.config()
        self.write("01-a.md", note("a", "A" * 40))
        r = self.check()
        self.assertEqual(r.returncode, 1)
        self.assertIn("card fits", r.stderr)

    def test_spine_must_be_a_real_edge(self):
        self.minimal()
        self.config(spine=["b", "a"])                          # backwards
        r = self.check()
        self.assertEqual(r.returncode, 1)
        self.assertIn("spine", r.stderr)


# ----------------------------------------------------------------- build
class TestBuild(Flow):
    def test_builds_and_embeds_every_note(self):
        self.minimal()
        self.assertEqual(self.build().returncode, 0)
        html = self.html()
        self.assertIn('id="note-a"', html)
        self.assertIn('id="note-b"', html)

    def test_output_is_self_contained(self):
        self.minimal()
        self.build()
        self.assertNotIn('src="http', self.html())
        self.assertNotIn('href="http', self.html())

    def test_standfirst_is_rendered(self):
        self.minimal()
        self.build()
        self.assertIn("A one sentence answer.", self.html())

    def test_reference_kind_is_embedded_but_not_drawn(self):
        self.config(kinds={"finding": {"tone": "plain", "label": "F"},
                           "reference": {"tone": "none", "label": "R"}})
        self.write("01-a.md", note("a", "A"))
        self.write("02-src.md", note("src", "Sources", kind="reference"))
        self.assertEqual(self.build().returncode, 0)
        html = self.html()
        self.assertIn('id="note-src"', html)          # searchable
        self.assertNotIn('data-note="src"', html)     # not a card

    def test_cycle_is_named_not_hung(self):
        self.config()
        self.write("01-a.md", note("a", "A", dep=["b"], unl=["b"]))
        self.write("02-b.md", note("b", "B", dep=["a"], unl=["a"]))
        r = self.build()
        self.assertEqual(r.returncode, 1)
        self.assertIn("cycle", r.stderr)


# ------------------------------------------- fixes the eval run uncovered
class TestCrossNoteLinks(Flow):
    """A markdown link to another note must actually open it. Before the fix
    the shell listened on popstate only, its click handler required
    [data-note], and #notes was display:none — so the link was a dead click."""

    def test_shell_opens_a_hash_link_that_names_a_note(self):
        shell = open(SHELL).read()
        self.assertTrue("hashchange" in shell,
                        "shell must react to a hash change, not popstate alone")
        self.assertTrue('a[href^="#"]' in shell,
                        "shell must intercept anchor links that name a note")

    def test_rendered_cross_link_is_reachable(self):
        self.config()
        self.write("01-a.md", note("a", "A", unl=["b"],
                                   body="# A\n\n## S\n\nSee [B](#b) for detail.\n"))
        self.write("02-b.md", note("b", "B", dep=["a"]))
        self.assertEqual(self.build().returncode, 0)
        self.assertIn('href="#b"', self.html())

    def test_section_rail_does_not_collide_with_note_ids(self):
        """Rail entries scroll within the panel; they must not be treated as
        note links, and must not depend on document-wide unique ids."""
        self.minimal()
        self.build()
        self.assertTrue("data-goto" in self.html(),
                        "rail entries should scroll by lookup inside the panel")


class TestLoopingFlows(Flow):
    """Real user flows loop — free tier -> banner -> paywall -> free tier.
    A loop edge is drawn but excluded from layering, so it neither creates a
    false cycle nor forces the author to leave a real path undrawn."""

    def test_loop_edge_is_allowed_and_drawn(self):
        self.config()
        self.write("01-a.md", note("a", "A", unl=["b"]))
        self.write("02-b.md", note("b", "B", dep=["a"], extra="loops_to: [a]\n"))
        r = self.check()
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.build().returncode, 0)
        self.assertTrue("loop" in self.html().lower(), "loop edge should be drawn")

    def test_loop_target_must_exist(self):
        self.config()
        self.write("01-a.md", note("a", "A", extra="loops_to: [nowhere]\n"))
        r = self.check()
        self.assertEqual(r.returncode, 1)
        self.assertIn("nowhere", r.stderr)


class TestTypography(Flow):
    """A's type structure — serif body, sans display, mono for data — carried
    on system fallbacks so the page still works with no network."""

    def test_type_roles_are_tokens(self):
        shell = open(SHELL).read()
        for token in ("--font-display", "--font-body", "--font-mono"):
            self.assertTrue(token in shell, token + " should be a token")

    def test_body_face_is_a_serif_with_real_fallbacks(self):
        shell = open(SHELL).read()
        self.assertTrue("Source Serif" in shell and "Georgia" in shell,
                        "serif body needs a named face and a system fallback")

    def test_self_contained_by_default(self):
        self.minimal()
        self.build()
        self.assertNotIn("fonts.googleapis.com", self.html())

    def test_webfonts_are_opt_in(self):
        self.config(webfonts=True)
        self.write("01-a.md", note("a", "A", unl=["b"]))
        self.write("02-b.md", note("b", "B", dep=["a"]))
        self.build()
        self.assertIn("fonts.googleapis.com", self.html())


class TestTimeline(Flow):
    """Epic-level order and dependency, drawn as a Gantt."""

    def gantt_flow(self):
        self.config(timeline={"units": 8, "unitLabel": "Week",
                              "bands": [{"from": 3, "to": 4, "label": "Away"}]},
                    spine=["a", "b"])
        self.write("01-a.md", note("a", "A", unl=["b"], extra="start: 1\nlength: 2\n"))
        self.write("02-b.md", note("b", "B", dep=["a"], extra="start: 3\nlength: 4\n"))

    def test_gantt_renders_when_timeline_configured(self):
        self.gantt_flow()
        self.assertEqual(self.check().returncode, 0, self.check().stderr)
        self.assertEqual(self.build().returncode, 0)
        html = self.html()
        self.assertIn("gantt", html.lower())
        self.assertIn("Away", html)

    def test_no_gantt_without_timing(self):
        self.minimal()
        self.build()
        self.assertNotIn('class="gantt"', self.html())

    def test_spine_rows_are_marked_critical(self):
        self.gantt_flow()
        self.build()
        self.assertIn("bar crit", self.html())

    def test_bar_beyond_the_timeline_is_an_error(self):
        self.config(timeline={"units": 4, "unitLabel": "Week"})
        self.write("01-a.md", note("a", "A", extra="start: 3\nlength: 9\n"))
        r = self.check()
        self.assertEqual(r.returncode, 1)
        self.assertIn("timeline", r.stderr.lower())

    def test_length_requires_start(self):
        self.config(timeline={"units": 6, "unitLabel": "Week"})
        self.write("01-a.md", note("a", "A", extra="length: 2\n"))
        r = self.check()
        self.assertEqual(r.returncode, 1)


class TestEpics(Flow):
    """The tracker join. `epics.json` is written by sync_epics.py, which is the
    only part of this skill that touches the network; everything below reads it
    off disk, so the build stays offline and a rebuild stays deterministic."""

    def epic_flow(self, state="closed", with_sidecar=True):
        self.config(timeline={"units": 8, "unitLabel": "Week"},
                    issueUrl="https://example.test/issues/")
        self.write("01-a.md", note("a", "A", unl=["b"], extra="start: 1\nlength: 2\nepic: 68\n"))
        self.write("02-b.md", note("b", "B", dep=["a"], extra="start: 3\nlength: 2\n"))
        if with_sidecar:
            self.write("epics.json", json.dumps({
                "repo": "o/r",
                "epics": {"68": {"number": 68, "title": "The epic", "state": state,
                                 "url": "https://example.test/issues/68",
                                 "subIssues": [{"number": 71, "title": "A child",
                                                "state": "closed",
                                                "url": "https://example.test/issues/71"}]}},
            }))

    def test_closed_epic_paints_its_bar_green(self):
        self.epic_flow()
        self.assertEqual(self.build().returncode, 0)
        self.assertIn('class="bar e-done"', self.html())

    def test_open_epic_keeps_the_ordinary_bar(self):
        self.epic_flow(state="open")
        self.build()
        html = self.html()
        # `e-done` also appears in the stylesheet and the legend, so the
        # assertion has to name the bar's own class list or it passes for free.
        self.assertNotIn('class="bar e-done"', html)
        self.assertIn('class="bar"', html)

    def test_a_note_with_no_epic_draws_hatched(self):
        self.epic_flow()
        self.build()
        self.assertIn('class="bar e-none"', self.html())

    def test_the_epic_and_its_children_are_linked_from_the_note(self):
        self.epic_flow()
        self.build()
        html = self.html()
        self.assertIn("https://example.test/issues/68", html)
        self.assertIn("https://example.test/issues/71", html)
        self.assertIn("A child", html)

    def test_a_closed_epic_counts_as_done_on_the_roadmap(self):
        """The note's own status is `proposed`. The tracker outranks it."""
        self.epic_flow()
        self.build()
        html = self.html()
        self.assertIn('data-note="a" data-cats="none" data-done="1"', html)
        self.assertIn('data-note="b" data-cats="none" data-done="0"', html)

    def test_no_sidecar_is_not_an_error(self):
        """A flow whose work is not on a tracker never runs the sync."""
        self.epic_flow(with_sidecar=False)
        self.assertEqual(self.check().returncode, 0)
        self.assertEqual(self.build().returncode, 0)
        self.assertNotIn('class="bar e-done"', self.html())

    def test_epic_missing_from_the_sidecar_warns(self):
        self.epic_flow(with_sidecar=False)
        r = self.check()
        self.assertEqual(r.returncode, 0)
        self.assertIn("sync_epics", r.stderr)

    def test_closed_as_not_planned_is_not_shipped(self):
        """GitHub gives an abandoned epic the same `state` as a shipped one."""
        self.config(timeline={"units": 8, "unitLabel": "Week"})
        self.write("01-a.md", note("a", "A", extra="start: 1\nlength: 2\nepic: 68\n"))
        self.write("epics.json", json.dumps({"repo": "o/r", "epics": {"68": {
            "number": 68, "title": "Dropped", "state": "closed",
            "stateReason": "not_planned", "url": "https://example.test/i/68",
            "subIssues": []}}}))
        self.build()
        html = self.html()
        self.assertNotIn('class="bar e-done"', html)
        self.assertIn("not planned", html)

    def test_scalar_epic_with_a_list_value_is_read_as_a_list(self):
        """`epic: [68, 70]` under the legacy key is still a list of two, not an
        error — a card holds the epics it accumulates."""
        self.config(timeline={"units": 8, "unitLabel": "Week"})
        self.write("01-a.md", note("a", "A", extra="start: 1\nepics: [68, 70]\n"))
        self.assertEqual(self.build().returncode, 0)

    def test_a_non_numeric_epic_is_an_error(self):
        self.config(timeline={"units": 4, "unitLabel": "Week"})
        self.write("01-a.md", note("a", "A", extra="start: 1\nepic: ladderboard\n"))
        r = self.check()
        self.assertEqual(r.returncode, 1)
        self.assertIn("issue number", r.stderr)


class TestVocabulary(Flow):
    """A kind is a noun. The two mistakes below only show up on screen, weeks
    after the vocabulary was written."""

    def test_a_lifecycle_kind_warns(self):
        self.config(kinds={"shipped": {"tone": "plain", "label": "Shipped"}})
        self.write("01-a.md", note("a", "A", kind="shipped"))
        r = self.check()
        self.assertEqual(r.returncode, 0)
        self.assertIn("lifecycle state", r.stderr)

    def test_a_lifecycle_label_warns_even_with_a_noun_key(self):
        self.config(kinds={"x": {"tone": "plain", "label": "Not built"}})
        self.write("01-a.md", note("a", "A", kind="x"))
        self.assertIn("lifecycle state", self.check().stderr)

    def test_two_used_kinds_sharing_a_tone_warn(self):
        self.config(kinds={"screen": {"tone": "plain", "label": "Screen"},
                           "page": {"tone": "plain", "label": "Page"}})
        self.write("01-a.md", note("a", "A", kind="screen", unl=["b"]))
        self.write("02-b.md", note("b", "B", kind="page", dep=["a"]))
        self.assertIn("identical swatches", self.check().stderr)

    def test_an_unused_default_kind_is_not_linted(self):
        """`kinds` is the defaults merged with the flow's own. An unused
        default draws no card and appears in no legend."""
        self.config(kinds={"screen": {"tone": "plain", "label": "Screen"}})
        self.write("01-a.md", note("a", "A", kind="screen"))
        r = self.check()
        self.assertNotIn("identical swatches", r.stderr)
        self.assertNotIn("lifecycle state", r.stderr)

    def test_a_noun_vocabulary_is_silent(self):
        self.config(kinds={"screen": {"tone": "plain", "label": "Screen"},
                           "decision": {"tone": "warn", "label": "Decision"}})
        self.write("01-a.md", note("a", "A", kind="screen", unl=["b"]))
        self.write("02-b.md", note("b", "B", kind="decision", dep=["a"]))
        r = self.check()
        self.assertNotIn("lifecycle state", r.stderr)
        self.assertNotIn("identical swatches", r.stderr)


class TestManyEpics(Flow):
    """A card is a durable thing; the epics it accumulates over its life are a
    list. One epic per card was the same category error as a lifecycle kind -
    a transient value stapled to a permanent noun."""

    def with_epics(self, states):
        """states: {num: state}. Builds a one-note flow whose note names them all."""
        nums = ", ".join(str(n) for n in states)
        self.config(timeline={"units": 8, "unitLabel": "Week"},
                    doneStatuses=["validated"])
        self.write("01-a.md", note("a", "A",
                   extra="start: 1\nlength: 2\nexecutor: unattended\nepics: [%s]\n" % nums))
        self.write("epics.json", json.dumps({"repo": "o/r", "epics": {
            str(n): {"number": n, "title": "E%d" % n, "state": st,
                     "stateReason": "", "url": "https://x/%d" % n,
                     "subIssues": [{"number": n * 10, "title": "child",
                                    "state": st, "url": "https://x/%d0" % n}]}
            for n, st in states.items()}}))

    def test_a_list_of_epics_builds(self):
        self.with_epics({68: "closed", 91: "open"})
        self.assertEqual(self.check().returncode, 0, self.check().stderr)
        self.assertEqual(self.build().returncode, 0)

    def test_a_shipped_epic_builds_the_card_even_with_an_open_one(self):
        """Settings shipped as #69; #91 opening does not un-build it."""
        self.with_epics({68: "closed", 91: "open"})
        self.build()
        html = self.html()
        self.assertIn('class="bar x-unattended e-done"', html)
        self.assertIn('data-note="a" data-cats="none" data-done="1"', html)

    def test_all_open_epics_is_in_progress_not_unbuilt(self):
        self.with_epics({91: "open", 92: "open"})
        self.build()
        html = self.html()
        # The bar is the plain executor fill: not green (nothing shipped) and
        # not hatched (work is filed, just not done).
        self.assertIn('class="bar x-unattended"', html)
        self.assertNotIn('class="bar x-unattended e-done"', html)
        self.assertNotIn('class="bar x-unattended e-none"', html)
        self.assertIn('<g id="node-a" class="node" data-note="a"', html)  # no unbuilt class

    def test_the_panel_lists_every_epic_and_its_children(self):
        self.with_epics({68: "closed", 91: "open"})
        self.build()
        html = self.html()
        for frag in ("https://x/68", "https://x/91", "https://x/680", "https://x/910"):
            self.assertIn(frag, html)

    def test_two_open_epics_do_not_error(self):
        """The old build refused [68, 70]; that refusal is gone."""
        self.with_epics({68: "open", 70: "open"})
        self.assertEqual(self.build().returncode, 0)

    def test_legacy_singular_epic_still_works(self):
        self.config(timeline={"units": 8, "unitLabel": "Week"})
        self.write("01-a.md", note("a", "A",
                   extra="start: 1\nlength: 2\nexecutor: unattended\nepic: 68\n"))
        self.write("epics.json", json.dumps({"repo": "o/r", "epics": {"68": {
            "number": 68, "title": "E", "state": "closed", "stateReason": "",
            "url": "https://x/68", "subIssues": []}}}))
        self.build()
        self.assertIn('class="bar x-unattended e-done"', self.html())

    def test_both_epic_and_epics_is_an_error(self):
        self.config(timeline={"units": 8, "unitLabel": "Week"})
        self.write("01-a.md", note("a", "A", extra="epic: 68\nepics: [69]\n"))
        r = self.check()
        self.assertEqual(r.returncode, 1)
        self.assertIn("both", r.stderr.lower())

    def test_a_non_numeric_entry_in_the_list_errors(self):
        self.config(timeline={"units": 8, "unitLabel": "Week"})
        self.write("01-a.md", note("a", "A", extra="epics: [68, ladder]\n"))
        r = self.check()
        self.assertEqual(r.returncode, 1)
        self.assertIn("issue number", r.stderr)


class TestUnbuilt(Flow):
    """"Nobody has written an epic for this" is read off the tracker, never
    declared as a kind - a kind that means "not built" stops being true the day
    the work lands."""

    def tracked_flow(self, second_extra="start: 3\nlength: 2\n"):
        self.config(timeline={"units": 8, "unitLabel": "Week"})
        self.write("01-a.md", note("a", "A", unl=["b"],
                                   extra="start: 1\nlength: 2\nepic: 68\n"))
        self.write("02-b.md", note("b", "B", dep=["a"], extra=second_extra))
        self.write("epics.json", json.dumps({"repo": "o/r", "epics": {"68": {
            "number": 68, "title": "T", "state": "open", "stateReason": "",
            "url": "https://example.test/i/68", "subIssues": []}}}))

    def test_scheduled_work_with_no_epic_is_drawn_unbuilt(self):
        self.tracked_flow()
        self.build()
        html = self.html()
        self.assertIn('<g id="node-b" class="node unbuilt" data-note="b"', html)
        self.assertIn('data-note="a"', html)
        self.assertNotIn('<g id="node-a" class="node unbuilt" data-note="a"', html)

    def test_a_note_off_the_timeline_is_never_unbuilt(self):
        """A screen that shipped before the map existed has no epic and no
        start. Marking it unbuilt would be the whole map wrong."""
        self.tracked_flow(second_extra="")
        self.build()
        self.assertNotIn('class="node unbuilt"', self.html())

    def test_done_work_with_no_epic_is_never_unbuilt(self):
        self.tracked_flow(second_extra="start: 3\nlength: 2\n")
        t = flowio_read = open(os.path.join(self.dir, "02-b.md")).read()
        self.write("02-b.md", t.replace("status: proposed", "status: validated"))
        self.build()
        self.assertNotIn('class="node unbuilt"', self.html())

    def test_a_flow_that_uses_no_epics_is_untouched(self):
        """A decision map or a plain roadmap must not suddenly go red."""
        self.config(timeline={"units": 8, "unitLabel": "Week"})
        self.write("01-a.md", note("a", "A", unl=["b"], extra="start: 1\nlength: 2\n"))
        self.write("02-b.md", note("b", "B", dep=["a"], extra="start: 3\nlength: 2\n"))
        self.build()
        self.assertNotIn('class="node unbuilt"', self.html())

    def test_the_legend_names_it(self):
        self.tracked_flow()
        self.build()
        self.assertIn("No epic written yet", self.html())


class TestBuiltContradiction(Flow):
    """A card cannot be red for "not built" and dimmed as built at once. It is
    always a data problem - the kind was never updated when the work settled -
    and nothing else in the toolchain can see it."""

    def gap_kinds(self, **kw):
        kw.setdefault("kinds", {"gap": {"tone": "danger", "label": "Not built"},
                                "finding": {"tone": "plain", "label": "Finding"}})
        self.config(**kw)

    def test_a_done_status_on_a_not_built_card_warns(self):
        self.gap_kinds(doneStatuses=["decided"])
        self.write("01-a.md", note("a", "A", kind="gap").replace(
            "status: proposed", "status: decided"))
        r = self.check()
        self.assertEqual(r.returncode, 0)
        self.assertIn("Dim what is built", r.stderr)

    def test_a_closed_epic_on_a_not_built_card_warns(self):
        self.gap_kinds(doneStatuses=["validated"])
        self.write("01-a.md", note("a", "A", kind="gap", extra="epic: 68\n"))
        self.write("epics.json", json.dumps({"repo": "o/r", "epics": {"68": {
            "number": 68, "title": "T", "state": "closed", "stateReason": "",
            "url": "https://example.test/i/68", "subIssues": []}}}))
        r = self.check()
        self.assertEqual(r.returncode, 0)
        self.assertIn("closed epic", r.stderr)

    def test_an_ordinary_done_card_is_silent(self):
        """Only danger-toned kinds assert a state the done switch can contradict."""
        self.gap_kinds(doneStatuses=["decided"])
        self.write("01-a.md", note("a", "A", kind="finding").replace(
            "status: proposed", "status: decided"))
        self.assertNotIn("Dim what is built", self.check().stderr)

    def test_a_not_built_card_that_is_not_done_is_silent(self):
        self.gap_kinds(doneStatuses=["validated"])
        self.write("01-a.md", note("a", "A", kind="gap"))
        self.assertNotIn("Dim what is built", self.check().stderr)


class TestRobustness(Flow):
    """Findings from the two-axis review."""

    def run_in_c_locale(self, script):
        env = dict(os.environ, LC_ALL="C", LANG="C", PYTHONUTF8="0",
                   PYTHONCOERCECLOCALE="0")
        return subprocess.run([sys.executable, script, self.dir],
                              capture_output=True, text=True, env=env)

    def test_non_ascii_note_survives_a_c_locale(self):
        """Notes are full of em dashes. Reading them without an explicit
        encoding raises UnicodeDecodeError, which subclasses ValueError — so it
        used to surface as the wholly false 'no frontmatter block'."""
        self.config()
        self.write("01-a.md", note("a", "A", body="# A \u2014 dash\n\n## S \u2014 here\n\nText \u2014 more.\n"))
        r = self.run_in_c_locale(CHECK)
        self.assertEqual(r.returncode, 0, r.stderr)
        r = self.run_in_c_locale(BUILD)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertNotIn("no frontmatter", r.stderr)

    def test_checker_rejects_a_tone_the_builder_cannot_draw(self):
        """check_flow gates the build, so a kind the builder would KeyError on
        has to fail here rather than there."""
        self.config(kinds={"finding": {"tone": "accent", "label": "F"}})
        self.write("01-a.md", note("a", "A"))
        r = self.check()
        self.assertEqual(r.returncode, 1)
        self.assertIn("accent", r.stderr)

    def test_start_without_length_is_still_drawn(self):
        """The checker accepted start with no length; the builder dropped the
        row silently. One unit is the honest default."""
        self.config(timeline={"units": 5, "unitLabel": "Week"})
        self.write("01-a.md", note("a", "A", extra="start: 2\n"))
        self.assertEqual(self.check().returncode, 0)
        self.assertEqual(self.build().returncode, 0)
        self.assertIn('class="gantt-row"', self.html())


if __name__ == "__main__":
    unittest.main(verbosity=2)
