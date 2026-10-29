// Lessons: one lint rule per recurring review finding, each naming the PR it
// came from. Each lesson is its own rule under this local `lessons` plugin,
// never an entry in `no-restricted-syntax`: ESLint does not merge one rule's
// options across config objects, so two such entries silently replace each other.
// Every rule here needs red and green fixtures in eslint.lessons.test.mjs.

const lesson = (selector, message) => ({
  meta: { type: "problem", schema: [] },
  create: (context) => ({ [selector]: (node) => context.report({ node, message }) }),
});

export const plugin = {
  rules: {
    // "short-name": lesson("<esquery selector>", "What goes wrong, and the PR it came from (#123)."),
  },
};

export const lessons = [
  { files: ["src/**/*.{js,jsx,ts,tsx}"], plugins: { lessons: plugin } },
  // One object per lesson, scoped to the files it guards:
  // { files: ["src/**/*.{ts,tsx}"], ignores: ["**/*.test.*"], rules: { "lessons/short-name": "error" } },
];
