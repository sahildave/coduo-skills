// Every lesson carries a red fixture (the pre-fix code, must report) and a
// green fixture (the fixed code, must stay silent). A rule with no entry in
// `cases`, or with an empty side, fails this suite.
import { describe, it } from "vitest";
import { RuleTester } from "eslint";
import { plugin } from "../eslint.lessons.mjs"; // adjust to the repo root

RuleTester.describe = describe;
RuleTester.it = it;
RuleTester.itOnly = it.only;

// TS fixtures: pass the repo's parser, e.g.
// new RuleTester({ languageOptions: { parser: (await import("typescript-eslint")).parser } })
const tester = new RuleTester();

const cases = {
  // "short-name": {
  //   invalid: [{ code: `<pre-fix code>`, errors: 1 }],
  //   valid: [`<fixed code>`],
  // },
};

describe("lessons", () => {
  it("every lesson has red and green fixtures, and every fixture has a lesson", () => {
    for (const name of Object.keys(plugin.rules)) {
      const c = cases[name];
      if (!c?.invalid?.length || !c?.valid?.length) {
        throw new Error(`lessons/${name} needs at least one invalid (red) and one valid (green) case`);
      }
    }
    for (const name of Object.keys(cases)) {
      if (!plugin.rules[name]) throw new Error(`cases.${name} has no rule in eslint.lessons.mjs`);
    }
  });

  for (const [name, rule] of Object.entries(plugin.rules)) {
    if (cases[name]) tester.run(name, rule, cases[name]);
  }
});
