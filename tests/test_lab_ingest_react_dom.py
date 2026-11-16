"""React DOM acceptance-test support in the project-lab ingest runner."""

from pathlib import Path

from code_engine.lab_ingest import _run_node_tests


def test_lab_ingest_runs_tsx_component_test_in_jsdom(tmp_path: Path):
    lab = tmp_path / "labs" / "LAB-REACT-TEST"
    src = tmp_path / "labs" / "_reference" / "LAB-REACT-TEST" / "src"
    tests = lab / "tests"
    lab.mkdir(parents=True)
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
import { ClickCounter } from '../../_reference/LAB-REACT-TEST/src/ClickCounter';

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
