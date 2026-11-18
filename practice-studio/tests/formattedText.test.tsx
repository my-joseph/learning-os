/** FormattedText renders Markdown headings as bold labels, never as raw "###". */
import assert from "node:assert";
import React from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { FormattedText } from "../src/components/FormattedText";

const html = renderToStaticMarkup(
  <FormattedText text={"### Requirements\n- keep order\n#### Return contract"} />
);
assert.doesNotMatch(html, /###/, "raw ### must not be shown");
assert.match(html, /font-semibold[^>]*>Requirements</);
assert.match(html, /font-semibold[^>]*>Return contract</);
assert.match(html, /keep order/);
console.log("formattedText tests passed");
