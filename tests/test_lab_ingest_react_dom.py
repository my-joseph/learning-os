"""React DOM acceptance-test support in the project-lab ingest runner."""

from pathlib import Path

from code_engine.lab_ingest import _run_node_tests


def test_lab_ingest_runs_tsx_component_test_in_jsdom(tmp_path: Path):
    lab = tmp_path / "lab"
    src = lab / "src"
    tests = lab / "tests"
    src.mkdir(parents=True)
    tests.mkdir()
    (src / "ClickCounter.tsx").write_text(
        """import React, { useState } from 'react';
export function ClickCounter() {
  const [count, setCount] = useState(0);
  return <button onClick={() => setCount((value) => value + 1)}>Count: {count}</button>;
}
""",
        encoding="utf-8",
    )
    test_file = tests / "M1.test.tsx"
    test_file.write_text(
        """import { test } from 'vitest';
import assert from 'node:assert';
import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ClickCounter } from '../src/ClickCounter';

test('renders and increments after a user click', async () => {
  const user = userEvent.setup();
  render(<ClickCounter />);
  await user.click(screen.getByRole('button', { name: 'Count: 0' }));
  assert.equal(screen.getByRole('button').textContent, 'Count: 1');
});
""",
        encoding="utf-8",
    )

    cases = _run_node_tests([test_file], lab, src)

    assert len(cases) == 1
    assert cases[0]["passed"], cases
    assert not (lab / "node_modules").exists()


def test_lab_ingest_can_load_reference_component_outside_lab_root(tmp_path: Path):
    lab = tmp_path / "lab"
    tests = lab / "tests"
    reference_src = tmp_path / "_reference" / "lab" / "src"
    tests.mkdir(parents=True)
    reference_src.mkdir(parents=True)
    (reference_src / "Notice.tsx").write_text(
        "import React from 'react';\nexport function Notice() { return <output>Saved</output>; }\n",
        encoding="utf-8",
    )
    test_file = tests / "M3.test.tsx"
    test_file.write_text(
        """import { test } from 'vitest';
import assert from 'node:assert';
import React from 'react';
import { render, screen } from '@testing-library/react';
const source = process.env.LAB_SRC_DIR;
const { Notice } = await import(`${source}/Notice.tsx`);
test('loads a component from the sibling reference workspace', () => {
  render(<Notice />);
  assert.equal(screen.getByText('Saved').textContent, 'Saved');
});
""",
        encoding="utf-8",
    )

    cases = _run_node_tests([test_file], lab, reference_src)

    assert len(cases) == 1
    assert cases[0]["passed"], cases
