# -*- coding: utf-8 -*-
"""
Builder module for PRG-T00 (Foundation Audit):
Generates production-grade, Gold Standard (v3) content for:
- PRG-T00 (Topic)
- PRG-T00-C01 (Chapter: Web Platform Fundamentals)
- PRG-T00-C01-U01 through U08 (8 Units)
Strictly adheres to Central Rules:
- Complete Practice Guide (Core Skills, Prior Units, Common Traps, Cross-Subject Connections)
- Active Recall Questions with toggles
- My Implementation & Mistake Log
- Native @Page mentions (zero unparsed [[ tokens)
- 100% English, zero markdown leaks
"""
import json
import re
from apply_rules_and_test_pages import (
    load_env,
    notion_request,
    get_all_blocks,
    rt,
    parse_rt,
    validate_blocks_clean,
    h2,
    h3,
    p_block,
    callout_block,
    quote_block,
    bullet,
    num_item,
    todo_item,
    toggle_block,
    code_block,
    divider_block,
    eq_block,
    replace_page_blocks,
)

def build_prg_t00_topic(id_map):
    return [
        callout_block(
            "**Topic Objective:** Audit and solidify foundational web platform engineering, client-server mechanics, semantic layout, and modern developer workflows.\n"
            "**Measurable Deliverable:** Build and audit a fully accessible, responsive, multi-page web application from scratch with semantic HTML5, modern CSS Grid/Flexbox, strict keyboard navigation, and version-controlled Git history without relying on tutorials.\n"
            "**Prerequisites:** None (Entry Gate for Software Engineering Curriculum) | **Linked Resources:** [[R001]] (`MDN HTML`), [[R002]] (`MDN CSS`), [[R003]] (`MDN JS Guide`), [[R004]] (`TypeScript Handbook`), [[R029]] (`Git Book`), [[R030]] (`MDN HTTP`), [[R033]] (`Web.dev Accessibility`)",
            id_map,
            color="blue_background",
        ),
        h2("1. Overview & Engineering Context", id_map),
        p_block(
            "[[PRG-T00]] (`Foundation Audit`) serves as the uncompromising baseline gate of the entire software engineering curriculum. Before writing complex React state in [[PRG-T02]], architecting Next.js Server Actions in [[PRG-T03]], or managing distributed databases in [[PRG-T05]], an engineer must command the underlying platform without abstraction leaks.",
            id_map,
        ),
        p_block(
            "Every modern framework compiles down to the fundamental triumvirate of the browser: HTML for semantic document trees, CSS for cascading layout engines, and JavaScript for runtime event-driven execution across the HTTP network boundary. Mastering these fundamentals transforms debugging from superstitious trial-and-error into predictable first-principles deduction.",
            id_map,
        ),
        divider_block(),
        h2("2. Measurable Learning Outcomes", id_map),
        bullet("**Platform Literacy & Network Protocols:** Trace the end-to-end lifecycle of a web request from DNS lookup, TCP/TLS handshake, HTTP header exchange, to browser Critical Rendering Path (DOM + CSSOM -> Render Tree -> Layout -> Paint -> Composite).", id_map),
        bullet("**Semantic Architecture & Accessibility (a11y):** Construct semantic document structures using HTML5 landmark elements, accessible forms, and ARIA roles that achieve 100% keyboard operability and WCAG 2.1 AA compliance.", id_map),
        bullet("**Predictable Layout & Cascade Systems:** Master the CSS Cascade, specificity calculation, box model, Flexbox 1D alignment, and CSS Grid 2D track placement without random hacking.", id_map),
        bullet("**Engineering Tooling & Version Control:** Confidently navigate the Unix CLI, configure npm package scripts, manage Git branches/merges, and resolve merge conflicts cleanly.", id_map),
        divider_block(),
        h2("3. Learning & Practice Architecture (Pedagogical Engine)", id_map),
        p_block(
            "This curriculum enforces an uncompromising engineering standard through a rigorous local development practice engine:",
            id_map,
        ),
        bullet("**The Local IDE Mandate:** Practice takes place entirely in the local terminal and VS Code cockpit. Students write production code, run test suites (`npm test`), request automated tech lead code reviews (`npm run review`), and submit work (`npm run submit`) directly from their local environment.", id_map),
        bullet("**Dual-Engine Evaluation:** Workspaces feature Dual-Tier validation: Visible / Contract unit tests for rapid TDD feedback, accompanied by Hidden dynamic trap tests that evaluate boundary invariants and prevent hardcoding.", id_map),
        bullet("**5 Real-World Drill Archetypes:**", id_map, children=[
            bullet("`Algorithmic / Pure Logic`: Invariant design, data structure manipulation, and computational complexity.", id_map),
            bullet("`Project-Based (Multi-Module)`: Architectural composition, state management, and decoupled component contracts.", id_map),
            bullet("`Refactoring Legacy Code`: Safely modernizing entangled legacy codebases while preserving 100% backward test compatibility.", id_map),
            bullet("`Bug Fixing & Edge Cases`: Systematic defect triage, stack trace diagnosis, and boundary condition hardening.", id_map),
            bullet("`Performance & Concurrency`: Optimizing latency, asynchronous queues, memory leaks, and sliding window rate limiters.", id_map),
        ]),
        bullet("**The 6-Step Pedagogical Practice Loop:**", id_map, children=[
            bullet("1. `Think Before Coding`: Sketch invariants, mental model, and boundary edge cases.", id_map),
            bullet("2. `Hands-On Implementation`: Write solution in local editor files.", id_map),
            bullet("3. `Automated Testing`: Run local test suites (`npm test`) to verify correctness.", id_map),
            bullet("4. `Code Review`: Explain the algorithm and request an AI Senior Tech Lead PR Review (`npm run review`).", id_map),
            bullet("5. `Refactor`: Decouple helper functions, improve readability, and optimize performance.", id_map),
            bullet("6. `Scale Difficulty`: Subject code to stress tests and harsher edge case inputs.", id_map),
        ]),
        divider_block(),
        h2("4. Chapter Sequence & Learning Path (3 Chapters)", id_map),
        num_item(
            "[[PRG-T00-C01]] — **Web Platform Fundamentals (8 Units):** Network request lifecycle, Semantic HTML5, CSS cascading specificity, Box model, Flexbox, Grid, Responsive design, Accessibility (a11y), and Browser DevTools.",
            id_map,
        ),
        num_item(
            "[[PRG-T00-C02]] — **JavaScript & TypeScript Baseline (7 Units):** Runtime memory types, scope, array/object manipulation, DOM manipulation, browser events, Promises, and introductory TypeScript compilation.",
            id_map,
        ),
        num_item(
            "[[PRG-T00-C03]] — **Developer Workflow & Git (6 Units):** Terminal shell commands, project file hierarchy, npm scripts, Git branches, commits, pull requests, and open-source issue workflows.",
            id_map,
        ),
        divider_block(),
        h2("5. Resources & Source Attribution", id_map),
        bullet("**Primary Reference Specifications:**", id_map, children=[
            bullet("[[R001]] — `MDN HTML Documentation`: Authoritative specification for HTML5 elements and semantic document hierarchies.", id_map),
            bullet("[[R002]] — `MDN CSS Documentation`: Definitive guide on CSS Cascade, specificity, Flexbox, and Grid layout specifications.", id_map),
            bullet("[[R003]] — `MDN JS Guide`: Authoritative guide to modern JavaScript syntax, runtime behavior, and APIs.", id_map),
            bullet("[[R004]] — `TypeScript Handbook`: Microsoft official TypeScript documentation and typing rules.", id_map),
            bullet("[[R029]] — `Pro Git Book`: Comprehensive reference on Git internals, branching, and collaboration by Scott Chacon.", id_map),
            bullet("[[R030]] — `MDN HTTP`: Authoritative reference for HTTP/1.1, HTTP/2, request/response headers, and caching models.", id_map),
            bullet("[[R033]] — `Web.dev Learn Accessibility`: Google Web Standards curriculum for accessible web development and WCAG 2.1 guidelines.", id_map),
        ]),
        divider_block(),
        h2("6. Cross-Subject Bridge to Upper Topics", id_map),
        bullet("**Bridge to [[PRG-T01]] (JavaScript & TypeScript Engineering):** The scope and event fundamentals introduced here provide the empirical grounding required for Execution Contexts, Closures, and Prototype Chains in [[PRG-T01-C01]].", id_map),
        bullet("**Bridge to [[PRG-T02]] & [[PRG-T03]] (React & Next.js Architecture):** Semantic landmarks, form labels, and CSS layout directly govern JSX component breakdown, accessible form actions, and responsive layout hierarchies in Next.js App Router.", id_map),
        divider_block(),
        h2("7. Final Review & Mastery Audit", id_map),
        todo_item("Audit and pass all 21 Units across [[PRG-T00-C01]], [[PRG-T00-C02]], and [[PRG-T00-C03]] with honest `Mastery (0-4)` >= 3.", id_map),
        todo_item("Build an unassisted, responsive capstone landing page verified against Google Lighthouse (Score 95+ on Accessibility and Best Practices) before marking [[PRG-T00]] as `Done`.", id_map),
    ]

def build_prg_t00_c01(id_map):
    return [
        callout_block(
            "**Chapter Objective:** Master core web platform mechanics: HTTP request lifecycle, semantic HTML5, CSS cascading specificity, Box model, Flexbox/Grid layouts, WCAG 2.1 AA accessibility, and Browser DevTools diagnostics.\n"
            "**Completion Criteria:** Build a responsive, accessible multi-section landing page featuring valid semantic landmarks, fluid layout, strict keyboard tab navigation, and zero DevTools console/network errors.\n"
            "**Parent Topic:** [[PRG-T00]] | **Sources:** [[R001]] (`MDN HTML`), [[R002]] (`MDN CSS`), [[R030]] (`MDN HTTP`), [[R033]] (`Web.dev Accessibility`)",
            id_map,
            color="blue_background",
        ),
        h2("1. Chapter Role & Web Platform Mental Model", id_map),
        p_block(
            "[[PRG-T00-C01]] establishes the runtime physics of the browser environment. The browser is not a magic canvas—it is a streaming parser and rendering pipeline governed by strict specifications:",
            id_map,
        ),
        num_item(
            "**The Critical Rendering Path (CRP):** The browser receives raw HTML byte streams over TCP, decodes characters, tokenizes HTML tags into nodes, and constructs the **Document Object Model (DOM)**. Concurrently, CSS stylesheets are fetched and parsed into the **CSS Object Model (CSSOM)**. Combining DOM and CSSOM produces the **Render Tree**, which calculates geometry (**Layout / Reflow**) and rasterizes pixels to screen (**Paint & Composite**).",
            id_map,
        ),
        num_item(
            "**Document Semantics vs. Visual Styling:** HTML provides meaning, accessibility tree nodes, and document outlines. CSS provides visual presentation. Conflating the two (e.g. styling a `<div>` to act like a button without keyboard listeners or ARIA roles) breaks screen readers, SEO crawlers, and native browser keyboard navigation.",
            id_map,
        ),
        divider_block(),
        h2("2. Core Web Platform Concepts & Invariants", id_map),
        bullet("**CSS Cascading Specificity Weight Matrix:**", id_map),
        p_block(
            "When multiple CSS rules target the same element, the browser calculates specificity as a 4-part tuple $(a, b, c, d)$:\n"
            "* $a$: Inline styles (`style=\"...\"`)\n"
            "* $b$: ID selectors (`#header`)\n"
            "* $c$: Class selectors (`.nav`), attribute selectors (`[type=\"text\"]`), and pseudo-classes (`:hover`, `:focus`)\n"
            "* $d$: Element selectors (`div`, `p`) and pseudo-elements (`::before`)",
            id_map,
        ),
        bullet("**The Box Model Standard Invariant:**", id_map),
        p_block(
            "Always enforce `box-sizing: border-box` globally. Under default `content-box`, declared `width` applies only to the inner content, causing `padding` and `border` to expand total element dimensions and trigger unexpected layout wrapping.",
            id_map,
        ),
        divider_block(),
        h2("3. Unit Sequence & Progression (8 Units)", id_map),
        num_item("[[PRG-T00-C01-U01]] — **How the Web Works:** DNS resolution, TCP/IP 3-way handshake, TLS negotiation, and HTTP/HTTPS request-response headers and status codes.", id_map),
        num_item("[[PRG-T00-C01-U02]] — **Semantic HTML:** Semantic landmark tags (`<header>`, `<nav>`, `<main>`, `<article>`, `<section>`, `<footer>`), forms, labels, and document outlines.", id_map),
        num_item("[[PRG-T00-C01-U03]] — **CSS Fundamentals:** Selectors, specificity calculation, inheritance, and the cascade algorithm.", id_map),
        num_item("[[PRG-T00-C01-U04]] — **Box Model and Layout:** Content, padding, border, margin collapse, normal flow, and CSS positioning (`relative`, `absolute`, `fixed`, `sticky`).", id_map),
        num_item("[[PRG-T00-C01-U05]] — **Flexbox and Grid:** 1D Flexbox axis alignment vs 2D CSS Grid tracks, auto-fit, and fractional units (`fr`).", id_map),
        num_item("[[PRG-T00-C01-U06]] — **Responsive Design:** Viewport meta tag, media queries, mobile-first design, fluid units (`rem`, `vw`, `vh`), and CSS `clamp()`.", id_map),
        num_item("[[PRG-T00-C01-U07]] — **Accessibility and Keyboard Navigation:** WCAG 2.1 AA contrast requirements, semantic focus rings, tabindex rules, and screen reader testing.", id_map),
        num_item("[[PRG-T00-C01-U08]] — **Browser DevTools:** Inspecting DOM/CSSOM, network waterfall analysis, payload inspection, and Lighthouse audits.", id_map),
        divider_block(),
        h2("4. Resources & Source Attribution", id_map),
        bullet("**Authoritative Sources:**", id_map, children=[
            bullet("[[R001]] — `MDN HTML Guide`: Definitive reference for all HTML5 semantic elements and attributes.", id_map),
            bullet("[[R002]] — `MDN CSS Guide`: Comprehensive guide on CSS layout, Grid, and Flexbox modules.", id_map),
            bullet("[[R030]] — `MDN HTTP`: Reference for headers, methods (GET, POST, PUT, DELETE), and status codes.", id_map),
            bullet("[[R033]] — `Web.dev Accessibility`: Standards for accessible semantic markup and WCAG 2.1 compliance.", id_map),
        ]),
        divider_block(),
        h2("5. Chapter Practice Guide", id_map),
        p_block("After studying the 8 Units in [[PRG-T00-C01]], use this blueprint to test and solidify your web platform mastery:", id_map),
        bullet("**1. Chapter Mixed Practice (Comprehensive Landing Page):**", id_map, children=[
            bullet("**Semantic Multi-Section Audit:** Code a complete landing page from scratch containing a sticky `<header>` with skip-nav link, hero section with fluid typography, responsive 3-column product grid using CSS Grid `repeat(auto-fit, minmax(...))`, contact form with explicit `<label for>` bindings, and footer. Zero frameworks or CSS libraries allowed.", id_map),
            bullet("**Lighthouse 95+ Audit:** Run Google Chrome DevTools Lighthouse audit; achieve 100% on Accessibility, 95+ on Best Practices, and zero layout shifts (CLS = 0).", id_map),
        ]),
        bullet("**2. Combine with Prior Units:**", id_map, children=[
            bullet("**Network & HTML Inspection:** Open DevTools Network tab, inspect the exact Content-Type headers, HTTP status codes, and gzip/brotli transfer sizes for all HTML, CSS, and asset requests.", id_map),
        ]),
        bullet("**3. Chapter-Wide Traps:**", id_map, children=[
            bullet("**Div-Soup Non-Semantic Anti-Pattern:** Using `<div class=\"btn\" onclick=\"...\">` instead of `<button type=\"button\">`, which completely breaks keyboard focus, Enter/Space activation, and screen readers.", id_map),
            bullet("**Margin Collapse Trap:** Unintended vertical spacing caused by margin collapsing between adjacent block siblings or parent/first-child elements.", id_map),
            bullet("**Unresponsive Pixel Traps:** Hardcoding fixed pixel widths (`width: 1200px`) instead of fluid percentages or `max-width: 100%`.", id_map),
            bullet("**Missing Visible Focus Trap:** Suppressing `:focus { outline: none; }` without providing an accessible high-contrast replacement focus indicator.", id_map),
        ]),
        bullet("**4. Cross-Subject & Real-World Connection (React & Next.js):**", id_map, children=[
            bullet("**Bridge to [[PRG-T02]] (React):** React components are direct abstractions of semantic HTML. A component hierarchy built on clean landmarks produces clean accessible React trees.", id_map),
            bullet("**Bridge to [[PRG-T03]] (Next.js):** Understanding HTTP status codes (200, 301, 404, 500) and caching headers directly underpins Next.js Route Handlers and Server Components.", id_map),
        ]),
        divider_block(),
        h2("6. Summary & Spaced Review Guide", id_map),
        todo_item("Complete all 8 Units in [[PRG-T00-C01]] and log personal code experiments and pitfalls in each Unit's `My Implementation & Mistake Log`.", id_map),
        todo_item("Pass the Chapter Practice Guide landing page audit before advancing to [[PRG-T00-C02]].", id_map),
    ]

def build_prg_t00_c01_u01(id_map):
    return [
        callout_block(
            "**Learning Objective:** Trace the complete request-response lifecycle across DNS resolution, TCP 3-way handshake, TLS encryption, HTTP/HTTPS headers, status codes, and browser rendering.\n"
            "**Expected Output:** Explain the end-to-end journey of typing a URL into the browser address bar to pixel rasterization, diagnose HTTP status codes, and analyze network waterfalls in DevTools.\n"
            "**Parent:** [[PRG-T00]] → [[PRG-T00-C01]] | **Next Unit:** [[PRG-T00-C01-U02]] | **Source:** [[R030]] (`MDN HTTP`)",
            id_map,
            color="blue_background",
        ),
        h2("1. Core Concepts & Architectural Mental Model", id_map),
        bullet("**1. DNS Resolution ([[CON-DNS]]):**", id_map, children=[
            bullet("When a user requests `https://example.com/api/users`, the browser first checks local [[CON-DNS]] caches (browser cache, OS cache, router cache). If not cached, it queries the recursive resolver, root nameserver, TLD nameserver (`.com`), and authoritative nameserver to resolve the domain to an IP address (e.g. `93.184.216.34`).", id_map),
        ]),
        bullet("**2. TCP Connection & TLS Handshake:**", id_map, children=[
            bullet("To establish a reliable connection over IP, the client and server execute a [[CON-TCP-HANDSHAKE]]: `SYN` (client) -> `SYN-ACK` (server) -> `ACK` (client).", id_map),
            bullet("For secure HTTPS (port 443), [[CON-TLS]] performs cryptographic key exchange to authenticate the server's certificate and establish symmetric encryption before application data travels.", id_map),
        ]),
        bullet("**3. HTTP Request & Response Anatomy ([[CON-HTTP]]):**", id_map, children=[
            bullet("**Request:** Method (`GET`, `POST`, `PUT`, `DELETE`, `PATCH`), URI path, HTTP version, and headers (`Host`, `User-Agent`, `Accept`, `Authorization`, `Cookie`).", id_map),
            bullet("**Response:** Status line (HTTP version, Status code, Reason phrase), headers (`Content-Type`, `Cache-Control`, `Set-Cookie`), and payload body.", id_map),
        ]),
        bullet("**4. Standard HTTP Status Code Classes:**", id_map, children=[
            bullet("`1xx` Informational: Request received, continuing process (e.g. `101 Switching Protocols` for [[CON-WEBSOCKET]]).", id_map),
            bullet("`2xx` Success: Action successfully received and accepted (`200 OK`, `201 Created`, `204 No Content`).", id_map),
            bullet("`3xx` Redirection: Further action needed (`301 Moved Permanently`, `302 Found`, `304 Not Modified` for cache hits).", id_map),
            bullet("`4xx` Client Error: Invalid client request (`400 Bad Request`, `401 Unauthorized`, `403 Forbidden`, `404 Not Found`, `429 Too Many Requests`).", id_map),
            bullet("`5xx` Server Error: Server failed to fulfill valid request (`500 Internal Server Error`, `502 Bad Gateway`, `503 Service Unavailable`, `504 Gateway Timeout`).", id_map),
        ]),
        divider_block(),
        h2("2. Code & Structure Examples", id_map),
        h3("Example 1: Raw HTTP/1.1 Request and Response Protocol Exchange", id_map),
        code_block(
            "// CLIENT REQUEST:\n"
            "GET /api/v1/profile HTTP/1.1\n"
            "Host: api.example.com\n"
            "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)\n"
            "Accept: application/json\n"
            "Authorization: Bearer eyJhbGciOiJIUzI1NiIsIn...\n"
            "Connection: keep-alive\n\n"
            "// SERVER RESPONSE:\n"
            "HTTP/1.1 200 OK\n"
            "Date: Thu, 05 Nov 2026 10:00:00 GMT\n"
            "Content-Type: application/json; charset=utf-8\n"
            "Content-Length: 78\n"
            "Cache-Control: private, max-age=3600\n"
            "Strict-Transport-Security: max-age=31536000; includeSubDomains\n\n"
            "{\n"
            "  \"id\": \"usr_9042\",\n"
            "  \"username\": \"alice_dev\",\n"
            "  \"email\": \"alice@example.com\",\n"
            "  \"role\": \"admin\"\n"
            "}",
            "plain text",
        ),
        divider_block(),
        h2("3. Practice Guide", id_map),
        p_block("Use this blueprint to drill network diagnostics and request-response lifecycle mastery:", id_map),
        bullet("**1. Core Skills to Drill:**", id_map, children=[
            bullet("**Status Code Triage:** Given ambiguous error symptoms (e.g., API gateway timeout vs. invalid JWT vs. stale cache vs. server crash), accurately identify whether the response should be `401`, `403`, `404`, `500`, `502`, or `504`.", id_map),
            bullet("**CURL Diagnostic Protocol:** Practice executing command-line `curl -v https://httpbin.org/get` and inspecting raw TLS handshake lines, request headers, and response status codes.", id_map),
        ]),
        bullet("**2. Combine with Prior Units:**", id_map, children=[
            bullet("**Bridge to [[PRG-T00-C01-U08]] (DevTools):** Locate Network tab timing metrics: Queuing, Stalled, DNS Lookup, Initial Connection, SSL Handshake, Time to First Byte (TTFB), and Content Download.", id_map),
        ]),
        bullet("**3. Common Traps & Edge Cases to Test:**", id_map, children=[
            bullet("**401 vs. 403 Distinction Trap:** Returning `401 Unauthorized` when the user is already authenticated but lacks permissions (must be `403 Forbidden`). `401` means 'Authentication required / unauthenticated'; `403` means 'Authenticated but access denied'.", id_map),
            bullet("**502 vs. 504 Gateway Distinction:** `502 Bad Gateway` means the upstream server returned an invalid/corrupt response; `504 Gateway Timeout` means the upstream server failed to respond within the allowed time limit.", id_map),
            bullet("**CORS Header Misconception:** CORS (`Access-Control-Allow-Origin`) is enforced by the **browser**, not the server. The server actually processes the request, but the browser blocks JavaScript from reading the response if headers are missing.", id_map),
        ]),
        bullet("**4. Cross-Subject & Real-World Connection (Next.js & Backend):**", id_map, children=[
            bullet("**Bridge to [[PRG-T03]] & [[PRG-T04]]:** Next.js App Router Route Handlers (`return NextResponse.json({ ... }, { status: 201 })`) and Express.js REST APIs rely directly on strict HTTP semantics.", id_map),
        ]),
        divider_block(),
        h2("4. Active Recall Questions", id_map),
        toggle_block(
            "1. What is the exact difference between HTTP 401 Unauthorized and HTTP 403 Forbidden?",
            [
                "HTTP 401 Unauthorized indicates that the request lacks valid authentication credentials (the client is anonymous or provided an expired/invalid token). HTTP 403 Forbidden indicates that the client's identity is authenticated and verified, but the server refuses to grant access because the user lacks sufficient permissions/roles for that resource."
            ],
            id_map,
        ),
        toggle_block(
            "2. What is Time to First Byte (TTFB) and what does a high TTFB indicate in network debugging?",
            [
                "TTFB is the duration from the moment the browser sends the HTTP request to the moment it receives the first byte of the response body. A high TTFB indicates latency in server-side processing, database query bottlenecks, or slow upstream proxy connections, whereas a high Content Download time indicates large payload sizes or constrained network bandwidth."
            ],
            id_map,
        ),
        toggle_block(
            "3. Why does HTTPS require a TLS handshake on top of the TCP connection?",
            [
                "TCP only guarantees reliable, ordered packet delivery over IP—all packets travel in unencrypted plain text susceptible to eavesdropping and tampering. The TLS handshake performs server authentication using digital certificates and establishes shared ephemeral encryption keys so all subsequent application data is encrypted symmetrically."
            ],
            id_map,
        ),
        divider_block(),
        h2("5. My Implementation & Mistake Log", id_map),
        quote_block("**Feynman One-Liner (Summarize How the Web Works in 1–2 sentences):**\n[Write your summary here after studying]", id_map),
        quote_block("**My Solution / Working / Code (Network request curl logs, header analysis notes):**\n[Paste your curl outputs or network traces here]", id_map),
        quote_block("**Mistake & Pitfall Log (Record HTTP header misconceptions or status code confusions):**\n- [Log mistakes and lessons learned here]", id_map),
        divider_block(),
        h2("6. Completion Checklist & Mastery Review", id_map),
        todo_item("Traced the lifecycle of a web request from DNS lookup to DOM/CSSOM render tree construction.", id_map),
        todo_item("Differentiated status codes across 2xx, 3xx, 4xx (especially 401 vs 403), and 5xx (502 vs 504).", id_map),
        todo_item("Answered all 3 Active Recall questions and documented notes in Section 5.", id_map),
        todo_item("Updated `Status` and `Mastery (0-4)` properties on this page.", id_map),
    ]

def build_prg_t00_c01_u02(id_map):
    return [
        callout_block(
            "**Learning Objective:** Author valid, semantic HTML5 document structures using landmark elements (`<header>`, `<nav>`, `<main>`, `<article>`, `<section>`, `<footer>`), accessible forms, and semantic text tags.\n"
            "**Expected Output:** Construct an accessible web page outline that communicates clear document hierarchy to screen readers and search engines without relying on non-semantic `<div>` containers.\n"
            "**Parent:** [[PRG-T00]] → [[PRG-T00-C01]] | **Prerequisites:** [[PRG-T00-C01-U01]] | **Next Unit:** [[PRG-T00-C01-U03]] | **Sources:** [[R001]] (`MDN HTML`), [[R033]] (`Web.dev Accessibility`)",
            id_map,
            color="blue_background",
        ),
        h2("1. Core Concepts & Architectural Mental Model", id_map),
        bullet("**1. Semantic Landmarks & Document Outline:**", id_map, children=[
            bullet("`<header>`: Introduces a page or section; typically contains headings, logo, or primary navigation.", id_map),
            bullet("`<nav>`: Encloses major navigation link groups. Screen readers provide keyboard shortcuts to jump directly between `<nav>` landmarks.", id_map),
            bullet("`<main>`: Wraps the central, unique content of the document. A page must have **only one** visible `<main>` landmark.", id_map),
            bullet("`<article>`: Represents a standalone, reusable piece of content (e.g. blog post, product card, forum comment) that makes sense independently outside the page context.", id_map),
            bullet("`<section>`: Groups thematically related content with a shared heading (`<h2>`–`<h6>`).", id_map),
            bullet("`<footer>>`: Closing metadata, copyright, colophon, and secondary links.", id_map),
        ]),
        bullet("**2. Semantic Forms & Interactive Controls:**", id_map, children=[
            bullet("Always bind `<label for=\"input-id\">` to `<input id=\"input-id\">`. Clicking the label focuses the input, and screen readers announce the label text on focus.", id_map),
            bullet("Use `<button type=\"submit|button|reset\">` for actions on the current page; use `<a href=\"...\">` strictly for navigation to a new URL.", id_map),
            bullet("Group related radio buttons or checkboxes inside `<fieldset>` with an explanatory `<legend>` title.", id_map),
        ]),
        divider_block(),
        h2("2. Code & Structure Examples", id_map),
        h3("Example 1: Accessible, Production-Grade Semantic Document Structure", id_map),
        code_block(
            "<!DOCTYPE html>\n"
            "<html lang=\"en\">\n"
            "<head>\n"
            "  <meta charset=\"UTF-8\">\n"
            "  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">\n"
            "  <title>Developer Hub — Semantic Architecture</title>\n"
            "</head>\n"
            "<body>\n"
            "  <!-- Skip link for keyboard accessibility -->\n"
            "  <a href=\"#main-content\" class=\"skip-link\">Skip to main content</a>\n\n"
            "  <header>\n"
            "    <a href=\"/\" aria-label=\"Company Homepage\"><strong>DevHub</strong></a>\n"
            "    <nav aria-label=\"Primary Navigation\">\n"
            "      <ul>\n"
            "        <li><a href=\"/tutorials\">Tutorials</a></li>\n"
            "        <li><a href=\"/docs\">Documentation</a></li>\n"
            "      </ul>\n"
            "    </nav>\n"
            "  </header>\n\n"
            "  <main id=\"main-content\">\n"
            "    <h1>Web Platform Engineering</h1>\n\n"
            "    <section aria-labelledby=\"featured-heading\">\n"
            "      <h2 id=\"featured-heading\">Featured Articles</h2>\n"
            "      <article>\n"
            "        <h3>Understanding the Critical Rendering Path</h3>\n"
            "        <p>How the browser parses HTML tokens and renders pixels.</p>\n"
            "        <a href=\"/articles/crp\">Read full article</a>\n"
            "      </article>\n"
            "    </section>\n\n"
            "    <section aria-labelledby=\"newsletter-heading\">\n"
            "      <h2 id=\"newsletter-heading\">Subscribe</h2>\n"
            "      <form action=\"/subscribe\" method=\"POST\">\n"
            "        <div>\n"
            "          <label for=\"subscriber-email\">Email Address (Required):</label>\n"
            "          <input type=\"email\" id=\"subscriber-email\" name=\"email\" required autocomplete=\"email\">\n"
            "        </div>\n"
            "        <button type=\"submit\">Subscribe Now</button>\n"
            "      </form>\n"
            "    </section>\n"
            "  </main>\n\n"
            "  <footer>\n"
            "    <p>&copy; 2026 DevHub Engineering. All rights reserved.</p>\n"
            "  </footer>\n"
            "</body>\n"
            "</html>",
            "html",
        ),
        divider_block(),
        h2("3. Practice Guide", id_map),
        p_block("Use this blueprint to drill semantic markup and accessibility architecture:", id_map),
        bullet("**1. Core Skills to Drill:**", id_map, children=[
            bullet("**Semantic Refactoring Drill:** Given a broken 'div-soup' template where buttons are styled `<span onclick=\"...\">` and headings are `<p class=\"h1\">`, refactor into clean semantic HTML5 with zero layout disruption.", id_map),
            bullet("**Form Accessibility Audit:** Audit form inputs for explicit `for`/`id` association, `autocomplete` tokens, and accessible error messages (`aria-describedby`).", id_map),
        ]),
        bullet("**2. Combine with Prior Units:**", id_map, children=[
            bullet("**Bridge to [[PRG-T00-C01-U01]]:** Notice how `<html lang=\"en\">` and `<meta charset=\"UTF-8\">` guide browser decoding of the initial byte stream.", id_map),
        ]),
        bullet("**3. Common Traps & Edge Cases to Test:**", id_map, children=[
            bullet("**The Div-Button Trap:** Using `<div class=\"btn\">Click</div>` instead of `<button>`. A `<div>` is not focusable via Tab, cannot be triggered by Enter or Space keys, and has no `role=\"button\"` in the accessibility tree.", id_map),
            bullet("**Heading Hierarchy Skipping Trap:** Jumping from `<h1>` directly to `<h3>` or `<h4>` for visual sizing. Always maintain consecutive heading order (`<h1>` -> `<h2>` -> `<h3>`) and use CSS classes for font sizing.", id_map),
            bullet("**Missing `<main>` or Multiple `<main>`:** Having multiple unhidden `<main>` tags violates the HTML specification. A page must have exactly one top-level `<main>` landmark.", id_map),
        ]),
        bullet("**4. Cross-Subject & Real-World Connection (React / Next.js):**", id_map, children=[
            bullet("**Bridge to [[PRG-T02]] & [[PRG-T03]]:** In Next.js `layout.tsx`, the root layout renders `<html>`, `<body>`, `<header>`, and `<footer>`, while `page.tsx` renders `<main>` and feature `<section>` landmarks.", id_map),
        ]),
        divider_block(),
        h2("4. Active Recall Questions", id_map),
        toggle_block(
            "1. Why should you use a native `<button>` element instead of a styled `<div>` with an onclick event?",
            [
                "A native `<button>` automatically provides built-in accessibility features: it is natively focusable via keyboard Tab, exposes the 'button' role to screen readers, activates on both Enter and Space keys, can be disabled with the 'disabled' attribute, and submits forms when placed inside a `<form>` without requiring custom JavaScript."
            ],
            id_map,
        ),
        toggle_block(
            "2. What is the semantic difference between `<article>` and `<section>`?",
            [
                "An `<article>` is a self-contained, independent composition that could theoretically be syndicated, distributed, or republished on another site (such as a blog post, news story, or product review card). A `<section>` is a thematic grouping of content that belongs to a larger document and should generally contain an explanatory heading (`<h2>`–`<h6>`)."
            ],
            id_map,
        ),
        divider_block(),
        h2("5. My Implementation & Mistake Log", id_map),
        quote_block("**Feynman One-Liner (Summarize Semantic HTML in your own words):**\n[Write your summary here after studying]", id_map),
        quote_block("**My Solution / Working / Code (HTML snippets, document outlines):**\n[Paste your semantic HTML experiments here]", id_map),
        quote_block("**Mistake & Pitfall Log (Record semantic tag misuse or heading order issues):**\n- [Log mistakes and lessons learned here]", id_map),
        divider_block(),
        h2("6. Completion Checklist & Mastery Review", id_map),
        todo_item("Constructed a valid semantic document using landmark elements (`<header>`, `<nav>`, `<main>`, `<section>`, `<footer>`).", id_map),
        todo_item("Associated all form inputs with explicit `<label for=\"...\">` bindings.", id_map),
        todo_item("Answered Active Recall questions and recorded personal notes in Section 5.", id_map),
        todo_item("Updated `Status` and `Mastery (0-4)` properties on this page.", id_map),
    ]
def build_prg_t00_c01_u03(id_map):
    return [
        callout_block(
            "**Learning Objective:** Master the CSS Cascade algorithm, selector specificity calculation $(a, b, c, d)$, inheritance rules, and the `!important` anti-pattern.\n"
            "**Expected Output:** Calculate specificity tuples on sight, resolve conflicting CSS declarations without `!important`, and structure clean, maintainable stylesheets.\n"
            "**Parent:** [[PRG-T00]] → [[PRG-T00-C01]] | **Prerequisites:** [[PRG-T00-C01-U02]] | **Next Unit:** [[PRG-T00-C01-U04]] | **Source:** [[R002]] (`MDN CSS`)",
            id_map,
            color="blue_background",
        ),
        h2("1. Core Concepts & Architectural Mental Model", id_map),
        bullet("**1. The CSS Cascade Algorithm (How Conflicts Are Resolved):**", id_map, children=[
            bullet("When multiple rules target the same element, the browser sorts declarations through 4 criteria in order: (1) Origin and Importance (`!important` vs author vs user-agent); (2) Specificity; (3) Order of Appearance (later rules win ties); (4) Scoped proximity.", id_map),
        ]),
        bullet("**2. Specificity Calculation Tuple $(a, b, c, d)$:**", id_map, children=[
            bullet("$a$ — Inline styles (`style=\"color: red\"`): Weight 1-0-0-0.", id_map),
            bullet("$b$ — ID Selectors (`#nav`): Weight 0-1-0-0.", id_map),
            bullet("$c$ — Class selectors (`.btn`), attribute selectors (`[type=\"submit\"]`), and pseudo-classes (`:hover`, `:first-child`, `:focus`): Weight 0-0-1-0.", id_map),
            bullet("$d$ — Element selectors (`h1`, `p`, `button`) and pseudo-elements (`::before`, `::after`): Weight 0-0-0-1.", id_map),
            bullet("*Universal selector (`*`) and combinators (`+`, `>`, `~`) carry (0, 0, 0, 0) specificity.*", id_map),
        ]),
        bullet("**3. CSS Inheritance Rules:**", id_map, children=[
            bullet("Typography properties (`color`, `font-family`, `font-size`, `line-height`, `text-align`) are inherited by children by default.", id_map),
            bullet("Box model and layout properties (`width`, `height`, `margin`, `padding`, `border`, `background`, `display`, `position`) are strictly non-inherited.", id_map),
        ]),
        divider_block(),
        h2("2. Code & Structure Examples", id_map),
        h3("Example 1: Specificity Conflict and Resolution Without `!important`", id_map),
        code_block(
            "/* 1. Selector Specificity Calculations */\n"
            "/* Specificity: (0, 0, 0, 1) - 1 element */\n"
            "button {\n"
            "  background-color: #64748b;\n"
            "  color: #ffffff;\n"
            "}\n\n"
            "/* Specificity: (0, 0, 1, 1) - 1 class + 1 element */\n"
            "button.primary {\n"
            "  background-color: #2563eb; /* Overrides element selector */\n"
            "}\n\n"
            "/* Specificity: (0, 0, 2, 0) - 1 class + 1 pseudo-class */\n"
            ".primary:hover {\n"
            "  background-color: #1d4ed8; /* (0, 0, 2, 0) beats (0, 0, 1, 1) */\n"
            "}\n\n"
            "/* Anti-Pattern: NEVER resort to !important to overcome specificity wars:\n"
            "   .modal-btn { background-color: purple !important; } */",
            "css",
        ),
        divider_block(),
        h2("3. Practice Guide", id_map),
        p_block("Use this blueprint to drill CSS specificity calculation and cascade mechanics:", id_map),
        bullet("**1. Core Skills to Drill:**", id_map, children=[
            bullet("**Specificity Tally Drills:** Calculate the exact 4-tuple specificity for complex selectors (e.g., `#main .sidebar nav ul li > a:hover` -> $(0, 1, 2, 4)$).", id_map),
            bullet("**Refactoring '!important':** Take legacy CSS polluted with `!important` flags and eliminate all of them by restructuring selector specificity cleanly.", id_map),
        ]),
        bullet("**2. Combine with Prior Units:**", id_map, children=[
            bullet("**Bridge to [[PRG-T00-C01-U02]]:** Notice how semantic markup keeps selectors shallow (`.nav-link` vs `div > div > ul > li > a`).", id_map),
        ]),
        bullet("**3. Common Traps & Edge Cases to Test:**", id_map, children=[
            bullet("**The Over-Qualified Selector Trap:** Writing `div#app.container ul.nav li a.link` which binds styling to a rigid HTML structure and inflates specificity unnecessarily.", id_map),
            bullet("**Order of Appearance Trap:** In a tie (e.g. `.class-a` and `.class-b`), the rule declared **later in the CSS file** wins, regardless of the order they appear in the HTML `class=\"class-b class-a\"` attribute.", id_map),
        ]),
        bullet("**4. Cross-Subject & Real-World Connection (Tailwind CSS):**", id_map, children=[
            bullet("**Bridge to [[PRG-T03]] & Tailwind CSS:** Utility-first CSS frameworks like Tailwind maintain flat $(0, 0, 1, 0)$ specificity for all utility classes to make overrides predictable.", id_map),
        ]),
        divider_block(),
        h2("4. Active Recall Questions", id_map),
        toggle_block(
            "1. Which selector has higher specificity: `#content .title` or `html body #main div.container h1`? Why?",
            [
                "`#content .title` has specificity (0, 1, 1, 0) [1 ID, 1 class, 0 elements]. `html body #main div.container h1` has specificity (0, 1, 1, 4) [1 ID, 1 class, 4 elements]. Since the ID and class counts are equal, the second selector wins due to having 4 element selectors in position d."
            ],
            id_map,
        ),
        toggle_block(
            "2. In the HTML `<p class=\"blue red\">Text</p>`, which color applies if `.blue { color: blue; }` is written below `.red { color: red; }` in the CSS stylesheet?",
            [
                "The text will be blue. When selectors have identical specificity (both `.blue` and `.red` are 0-0-1-0), the order of classes in the HTML attribute is completely irrelevant—the rule that appears later in the CSS stylesheet wins the cascade tie-breaker."
            ],
            id_map,
        ),
        divider_block(),
        h2("5. My Implementation & Mistake Log", id_map),
        quote_block("**Feynman One-Liner (Summarize CSS Specificity in your own words):**\n[Write your summary here after studying]", id_map),
        quote_block("**My Solution / Working / Code (Specificity worksheets, selector tests):**\n[Paste your selector calculations here]", id_map),
        quote_block("**Mistake & Pitfall Log (Record cascade overrides or !important habits):**\n- [Log mistakes and lessons learned here]", id_map),
        divider_block(),
        h2("6. Completion Checklist & Mastery Review", id_map),
        todo_item("Calculated specificity tuples across ID, class, attribute, and element selectors.", id_map),
        todo_item("Understood why `!important` breaks stylesheet maintainability and resolved styling conflicts cleanly.", id_map),
        todo_item("Answered Active Recall questions and recorded personal notes in Section 5.", id_map),
        todo_item("Updated `Status` and `Mastery (0-4)` properties on this page.", id_map),
    ]

def build_prg_t00_c01_u04(id_map):
    return [
        callout_block(
            "**Learning Objective:** Master the CSS Box Model (`content`, `padding`, `border`, `margin`), `box-sizing: border-box`, vertical margin collapse, display modes (`block`, `inline`, `inline-block`, `none`), and positioning (`static`, `relative`, `absolute`, `fixed`, `sticky`).\n"
            "**Expected Output:** Accurately calculate computed box dimensions, predict margin collapse behavior, and build overlay/sticky layouts using CSS positioning.\n"
            "**Parent:** [[PRG-T00]] → [[PRG-T00-C01]] | **Prerequisites:** [[PRG-T00-C01-U03]] | **Next Unit:** [[PRG-T00-C01-U05]] | **Source:** [[R002]] (`MDN CSS`)",
            id_map,
            color="blue_background",
        ),
        h2("1. Core Concepts & Architectural Mental Model", id_map),
        bullet("**1. The Four Layers of the Box Model:**", id_map, children=[
            bullet("**Content:** Where text and child elements render.", id_map),
            bullet("**Padding:** Transparent breathing room between content and border.", id_map),
            bullet("**Border:** Line wrapping the padding and content.", id_map),
            bullet("**Margin:** Transparent clearance outside the border separating sibling elements.", id_map),
        ]),
        bullet("**2. `box-sizing: border-box` vs. `content-box`:**", id_map, children=[
            bullet("`content-box` (default): Declared `width` = content width. Total rendered width = `width + padding-left + padding-right + border-left + border-right`.", id_map),
            bullet("`border-box` (production standard): Declared `width` = total rendered width including padding and border. Content shrinks to accommodate padding, preventing unwanted layout wrapping.", id_map),
        ]),
        bullet("**3. Vertical Margin Collapse:**", id_map, children=[
            bullet("Adjoining top and bottom margins of block elements in the normal flow collapse into a single margin equal to $\\max(\\text{margin}_1, \\text{margin}_2)$, rather than adding together.", id_map),
            bullet("Margins do NOT collapse between flex items, grid items, or elements with `overflow: hidden` / borders between them.", id_map),
        ]),
        bullet("**4. CSS Positioning Schemes:**", id_map, children=[
            bullet("`static` (default): Normal document flow.", id_map),
            bullet("`relative`: Positioned relative to normal flow position without affecting surrounding flow.", id_map),
            bullet("`absolute`: Removed from normal flow; positioned relative to nearest positioned ancestor (`position != static`).", id_map),
            bullet("`fixed`: Removed from flow; positioned relative to viewport (stays fixed during scroll).", id_map),
            bullet("`sticky`: Hybrid; treated as relative until scroll reaches threshold, then behaves like fixed within its parent container.", id_map),
        ]),
        divider_block(),
        h2("2. Code & Structure Examples", id_map),
        h3("Example 1: Global Box-Sizing Reset and Modal / Sticky Header Patterns", id_map),
        code_block(
            "/* 1. Production Global Box-Sizing Reset */\n"
            "html {\n"
            "  box-sizing: border-box;\n"
            "}\n"
            "*, *::before, *::after {\n"
            "  box-sizing: inherit;\n"
            "  margin: 0;\n"
            "  padding: 0;\n"
            "}\n\n"
            "/* 2. Sticky Navigation Header */\n"
            ".site-header {\n"
            "  position: sticky;\n"
            "  top: 0;\n"
            "  z-index: 100;\n"
            "  background-color: #ffffff;\n"
            "  border-bottom: 1px solid #e2e8f0;\n"
            "}\n\n"
            "/* 3. Absolute Centered Modal Overlay */\n"
            ".modal-backdrop {\n"
            "  position: fixed;\n"
            "  inset: 0; /* top: 0; right: 0; bottom: 0; left: 0 */\n"
            "  background-color: rgba(0, 0, 0, 0.5);\n"
            "  display: flex;\n"
            "  align-items: center;\n"
            "  justify-content: center;\n"
            "}\n"
            ".modal-card {\n"
            "  width: 100%;\n"
            "  max-width: 500px;\n"
            "  padding: 24px;\n"
            "  background: white;\n"
            "  border-radius: 8px;\n"
            "}",
            "css",
        ),
        divider_block(),
        h2("3. Practice Guide", id_map),
        p_block("Use this blueprint to drill box model calculations and positioning mechanics:", id_map),
        bullet("**1. Core Skills to Drill:**", id_map, children=[
            bullet("**Dimension Calculation:** Calculate exact rendered dimensions under `content-box` vs `border-box` for an element with `width: 300px`, `padding: 20px`, and `border: 2px`.", id_map),
            bullet("**Margin Collapse Prevention:** Identify when margin collapse occurs and resolve it using `gap` in Flexbox/Grid or padding.", id_map),
        ]),
        bullet("**2. Combine with Prior Units:**", id_map, children=[
            bullet("**Bridge to [[PRG-T00-C01-U03]]:** Combine positioning with specificity to control modal overlay `z-index` stacking contexts.", id_map),
        ]),
        bullet("**3. Common Traps & Edge Cases to Test:**", id_map, children=[
            bullet("**The Forgotten Positioned Parent Trap:** Setting `position: absolute; top: 0; right: 0;` on a badge and wondering why it aligns to the top of the entire webpage instead of its parent card (because the parent lacked `position: relative`).", id_map),
            bullet("**The Sticky Stacking Context Trap:** `position: sticky` fails to stick if any parent ancestor has `overflow: hidden`, `overflow: auto`, or `overflow: scroll`.", id_map),
        ]),
        bullet("**4. Cross-Subject & Real-World Connection (React / Next.js):**", id_map, children=[
            bullet("**Bridge to [[PRG-T02]] (React Portals):** Modals often require rendering via React Portals to document `<body>` to break out of parent overflow/clipping contexts.", id_map),
        ]),
        divider_block(),
        h2("4. Active Recall Questions", id_map),
        toggle_block(
            "1. If an element has `width: 200px`, `padding: 20px`, `border: 5px`, and `margin: 15px`, what is its total rendered horizontal space under `content-box` vs `border-box`?",
            [
                "Under `content-box`: Total width = 200 (content) + 40 (padding) + 10 (border) = 250px (plus 30px margins = 280px space). Under `border-box`: Total width = 200px strictly, with content shrinking to 200 - 40 - 10 = 150px (plus 30px margins = 230px space)."
            ],
            id_map,
        ),
        toggle_block(
            "2. Why does an element with `position: sticky; top: 0;` fail to stick when scrolling if its parent has `overflow: hidden`?",
            [
                "`position: sticky` binds its scrolling context to its nearest scrolling ancestor. If an ancestor has `overflow: hidden`, `auto`, or `scroll`, the sticky element treats that ancestor as its scrolling box instead of the main viewport, preventing it from sticking to the page."
            ],
            id_map,
        ),
        divider_block(),
        h2("5. My Implementation & Mistake Log", id_map),
        quote_block("**Feynman One-Liner (Summarize CSS Box Model & Positioning in your own words):**\n[Write your summary here after studying]", id_map),
        quote_block("**My Solution / Working / Code (Box model calculations, layout experiments):**\n[Paste your layout code here]", id_map),
        quote_block("**Mistake & Pitfall Log (Record margin collapse or sticky positioning traps):**\n- [Log mistakes and lessons learned here]", id_map),
        divider_block(),
        h2("6. Completion Checklist & Mastery Review", id_map),
        todo_item("Configured a global `box-sizing: border-box` reset in CSS.", id_map),
        todo_item("Built a sticky header and an absolute-positioned overlay with relative parent container.", id_map),
        todo_item("Answered Active Recall questions and recorded personal notes in Section 5.", id_map),
        todo_item("Updated `Status` and `Mastery (0-4)` properties on this page.", id_map),
    ]
def build_prg_t00_c01_u05(id_map):
    return [
        callout_block(
            "**Learning Objective:** Master 1-dimensional Flexbox layout (main axis, cross axis, `justify-content`, `align-items`, `flex: 1 1 auto`) and 2-dimensional CSS Grid (`grid-template-columns`, `repeat(auto-fit, minmax(...))`, `grid-template-areas`, `gap`).\n"
            "**Expected Output:** Choose correctly between Flexbox and Grid, build complex 2D responsive dashboards without media queries, and center elements effortlessly.\n"
            "**Parent:** [[PRG-T00]] → [[PRG-T00-C01]] | **Prerequisites:** [[PRG-T00-C01-U04]] | **Next Unit:** [[PRG-T00-C01-U06]] | **Source:** [[R002]] (`MDN CSS`)",
            id_map,
            color="blue_background",
        ),
        h2("1. Core Concepts & Architectural Mental Model", id_map),
        bullet("**1. When to Use Flexbox vs. CSS Grid:**", id_map, children=[
            bullet("**Flexbox (1D — Row OR Column):** Optimal for aligning items along a single axis—navigation bars, button groups, icon-text pairs, centered content.", id_map),
            bullet("**CSS Grid (2D — Rows AND Columns Simultaneously):** Optimal for holistic page layouts, dashboard card grids, image galleries, and multi-track alignment where items must align across both axes.", id_map),
        ]),
        bullet("**2. Flexbox Axes & Alignment Properties:**", id_map, children=[
            bullet("`flex-direction`: Defines the **Main Axis** (`row` = horizontal, `column` = vertical). The perpendicular axis is the **Cross Axis**.", id_map),
            bullet("`justify-content`: Distributes extra space along the **Main Axis** (`flex-start`, `center`, `space-between`, `space-around`).", id_map),
            bullet("`align-items`: Aligns items along the **Cross Axis** (`stretch`, `center`, `flex-start`, `baseline`).", id_map),
            bullet("`flex: <grow> <shrink> <basis>`: Shorthand controlling how items expand (`flex-grow`), compress (`flex-shrink`), and default size (`flex-basis`).", id_map),
        ]),
        bullet("**3. CSS Grid Modern Layout Patterns:**", id_map, children=[
            bullet("`grid-template-columns: repeat(auto-fit, minmax(280px, 1fr))` creates an intrinsically responsive grid that automatically wraps columns without writing a single media query.", id_map),
            bullet("`gap`: Native, gap-safe spacing between rows and columns that never causes margin collapse.", id_map),
        ]),
        divider_block(),
        h2("2. Code & Structure Examples", id_map),
        h3("Example 1: Flexbox Navbar and Auto-Responsive CSS Grid Cards", id_map),
        code_block(
            "/* 1. Flexbox Navigation Bar */\n"
            ".navbar {\n"
            "  display: flex;\n"
            "  align-items: center;\n"
            "  justify-content: space-between;\n"
            "  padding: 1rem 2rem;\n"
            "  gap: 1.5rem;\n"
            "}\n"
            ".nav-links {\n"
            "  display: flex;\n"
            "  gap: 1rem;\n"
            "  list-style: none;\n"
            "}\n\n"
            "/* 2. Intrinsically Responsive 2D Grid (Zero Media Queries Required) */\n"
            ".card-grid {\n"
            "  display: grid;\n"
            "  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));\n"
            "  gap: 1.5rem;\n"
            "  padding: 2rem;\n"
            "}\n"
            ".card {\n"
            "  display: flex;\n"
            "  flex-direction: column;\n"
            "  justify-content: space-between;\n"
            "  padding: 1.5rem;\n"
            "  background: #f8fafc;\n"
            "  border-radius: 0.5rem;\n"
            "}",
            "css",
        ),
        divider_block(),
        h2("3. Practice Guide", id_map),
        p_block("Use this blueprint to drill Flexbox alignment and CSS Grid track positioning:", id_map),
        bullet("**1. Core Skills to Drill:**", id_map, children=[
            bullet("**Intrinsic Responsive Grid:** Build a responsive product catalog grid using `repeat(auto-fit, minmax(250px, 1fr))` and test layout on mobile (360px), tablet (768px), and wide desktop (1440px).", id_map),
            bullet("**Sticky Footer via Flexbox:** Implement a classic flexbox sticky footer layout (`display: flex; flex-direction: column; min-height: 100vh;` on body, `flex: 1;` on main).", id_map),
        ]),
        bullet("**2. Combine with Prior Units:**", id_map, children=[
            bullet("**Bridge to [[PRG-T00-C01-U04]]:** Notice how `gap` in Flexbox/Grid completely replaces tricky margin offsets.", id_map),
        ]),
        bullet("**3. Common Traps & Edge Cases to Test:**", id_map, children=[
            bullet("**`auto-fit` vs. `auto-fill` Trap:** `auto-fill` creates empty phantom columns if there are few items; `auto-fit` stretches existing items to fill the remaining track space.", id_map),
            bullet("**Minimum Content Overflow in Flexbox:** Flex items default to `min-width: auto`, which prevents children with long unbreaking strings from shrinking. Fix with `min-width: 0;` on the flex child.", id_map),
        ]),
        bullet("**4. Cross-Subject & Real-World Connection (Tailwind CSS):**", id_map, children=[
            bullet("**Bridge to [[PRG-T03]]:** Tailwind classes `flex items-center justify-between` and `grid grid-cols-1 md:grid-cols-3 gap-6` map directly to these Flexbox/Grid properties.", id_map),
        ]),
        divider_block(),
        h2("4. Active Recall Questions", id_map),
        toggle_block(
            "1. When would you choose CSS Grid over Flexbox?",
            [
                "Choose CSS Grid when you need a 2-dimensional layout where items must align along both rows AND columns simultaneously (such as dashboards, image galleries, or complex magazine layouts). Choose Flexbox for 1-dimensional layouts where items only need to distribute or align along a single axis (such as navbars, button groups, or centering a modal)."
            ],
            id_map,
        ),
        toggle_block(
            "2. How does `min-width: 0;` solve the common flex item text overflow bug?",
            [
                "By default, flex items have `min-width: auto`, meaning a flex item will never shrink smaller than the intrinsic width of its content (such as a long URL or preformatted code). Adding `min-width: 0` explicitly allows the flex item to shrink below its content's intrinsic width, enabling text truncation (`text-overflow: ellipsis`) and word wrapping."
            ],
            id_map,
        ),
        divider_block(),
        h2("5. My Implementation & Mistake Log", id_map),
        quote_block("**Feynman One-Liner (Summarize Flexbox vs Grid in your own words):**\n[Write your summary here after studying]", id_map),
        quote_block("**My Solution / Working / Code (Flexbox and Grid layout snippets):**\n[Paste your layout code here]", id_map),
        quote_block("**Mistake & Pitfall Log (Record flex axis confusion or grid track bugs):**\n- [Log mistakes and lessons learned here]", id_map),
        divider_block(),
        h2("6. Completion Checklist & Mastery Review", id_map),
        todo_item("Built an intrinsically responsive card grid using `auto-fit` and `minmax()`.", id_map),
        todo_item("Implemented a sticky footer layout using flexbox `min-height: 100vh`.", id_map),
        todo_item("Answered Active Recall questions and recorded personal notes in Section 5.", id_map),
        todo_item("Updated `Status` and `Mastery (0-4)` properties on this page.", id_map),
    ]

def build_prg_t00_c01_u06(id_map):
    return [
        callout_block(
            "**Learning Objective:** Master responsive design principles: viewport meta tag, mobile-first media queries (`min-width`), relative units (`rem`, `em`, `vw`, `vh`), and fluid typography using CSS `clamp()`.\n"
            "**Expected Output:** Engineer websites that adapt smoothly across any device viewport width (320px to 4K) without horizontal overflow or device-specific breakpoints.\n"
            "**Parent:** [[PRG-T00]] → [[PRG-T00-C01]] | **Prerequisites:** [[PRG-T00-C01-U05]] | **Next Unit:** [[PRG-T00-C01-U07]] | **Source:** [[R002]] (`MDN CSS`)",
            id_map,
            color="blue_background",
        ),
        h2("1. Core Concepts & Architectural Mental Model", id_map),
        bullet("**1. The Mandatory Viewport Meta Tag:**", id_map, children=[
            bullet("Without `<meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">`, mobile browsers render desktop-width pages (typically 980px) and zoom out, breaking all media queries.", id_map),
        ]),
        bullet("**2. Mobile-First Media Queries (`min-width`):**", id_map, children=[
            bullet("Write baseline CSS for small screens first without media queries. Use `@media (min-width: 768px)` to progressively enhance layouts for larger screens.", id_map),
            bullet("Avoid Desktop-First (`max-width`) because it forces mobile devices to parse and override desktop rules.", id_map),
        ]),
        bullet("**3. Relative Units & Fluid Typography (`clamp`):**", id_map, children=[
            bullet("`rem` (root em): Scales relative to root `<html>` font-size (default 16px). Respects user browser accessibility font preferences.", id_map),
            bullet("`clamp(MIN, VAL, MAX)`: Dynamically scales properties between bounds without discrete breakpoint jumps (e.g., `font-size: clamp(1.5rem, 4vw + 1rem, 3rem)`).", id_map),
        ]),
        divider_block(),
        h2("2. Code & Structure Examples", id_map),
        h3("Example 1: Mobile-First Responsive Breakpoints and Fluid Type", id_map),
        code_block(
            "/* 1. Fluid Typography without Breakpoint Jumps */\n"
            "h1 {\n"
            "  font-size: clamp(2rem, 5vw + 1rem, 4rem);\n"
            "  line-height: 1.15;\n"
            "}\n\n"
            "/* 2. Mobile-First Progression */\n"
            "/* Base: 1-column mobile layout */\n"
            ".container {\n"
            "  width: 100%;\n"
            "  padding: 1rem;\n"
            "}\n"
            ".sidebar {\n"
            "  display: none;\n"
            "}\n\n"
            "/* Tablet Enhancement (>= 768px) */\n"
            "@media (min-width: 768px) {\n"
            "  .container {\n"
            "    display: grid;\n"
            "    grid-template-columns: 240px 1fr;\n"
            "    gap: 2rem;\n"
            "  }\n"
            "  .sidebar {\n"
            "    display: block;\n"
            "  }\n"
            "}\n\n"
            "/* Desktop Enhancement (>= 1024px) */\n"
            "@media (min-width: 1024px) {\n"
            "  .container {\n"
            "    max-width: 1200px;\n"
            "    margin-inline: auto;\n"
            "  }\n"
            "}",
            "css",
        ),
        divider_block(),
        h2("3. Practice Guide", id_map),
        p_block("Use this blueprint to drill responsive workflows and fluid scaling:", id_map),
        bullet("**1. Core Skills to Drill:**", id_map, children=[
            bullet("**Horizontal Overflow Elimination:** Inspect pages in Chrome DevTools Device Mode; identify and fix causes of horizontal scrolling (unbounded widths, fixed pixel images).", id_map),
            bullet("**Fluid Container Tuning:** Combine `max-width: 100%`, `margin-inline: auto`, and `clamp()` to produce fluid pages.", id_map),
        ]),
        bullet("**2. Combine with Prior Units:**", id_map, children=[
            bullet("**Bridge to [[PRG-T00-C01-U05]]:** Combine Grid `auto-fit` with media queries for complex nested components.", id_map),
        ]),
        bullet("**3. Common Traps & Edge Cases to Test:**", id_map, children=[
            bullet("**Device-Specific Breakpoint Trap:** Targeting specific phones (e.g. `@media (width: 375px)`). Breakpoints should be determined by when **content breaks**, not specific hardware models.", id_map),
            bullet("**Pixels for Font Size Trap:** Hardcoding `font-size: 16px` on `<html>` overrides user accessibility settings in browser preferences.", id_map),
        ]),
        bullet("**4. Cross-Subject & Real-World Connection (Next.js & Tailwind):**", id_map, children=[
            bullet("**Bridge to [[PRG-T03]]:** Tailwind CSS uses the mobile-first philosophy exclusively (`md:grid-cols-2 lg:grid-cols-4`).", id_map),
        ]),
        divider_block(),
        h2("4. Active Recall Questions", id_map),
        toggle_block(
            "1. Why is Mobile-First (`min-width`) preferred over Desktop-First (`max-width`)?",
            [
                "Mobile-First aligns with the principle of progressive enhancement: simpler, leaner CSS is loaded and rendered by default for resource-constrained mobile devices, while richer styling and multi-column grid tracks are layered on only when viewport real estate permits. It avoids heavy style overrides."
            ],
            id_map,
        ),
        toggle_block(
            "2. How does `clamp(1rem, 2.5vw, 2rem)` calculate its value across screen sizes?",
            [
                "The browser continuously evaluates `2.5vw` (2.5% of viewport width). If `2.5vw` is smaller than `1rem`, it clamps to `1rem`. If `2.5vw` exceeds `2rem`, it clamps to `2rem`. In between, it scales smoothly without abrupt media query jumps."
            ],
            id_map,
        ),
        divider_block(),
        h2("5. My Implementation & Mistake Log", id_map),
        quote_block("**Feynman One-Liner (Summarize Responsive Design in your own words):**\n[Write your summary here after studying]", id_map),
        quote_block("**My Solution / Working / Code (Responsive media queries, clamp formulas):**\n[Paste your responsive experiments here]", id_map),
        quote_block("**Mistake & Pitfall Log (Record horizontal scroll bugs or breakpoint issues):**\n- [Log mistakes and lessons learned here]", id_map),
        divider_block(),
        h2("6. Completion Checklist & Mastery Review", id_map),
        todo_item("Included the standard viewport meta tag in all HTML files.", id_map),
        todo_item("Wrote mobile-first media queries without horizontal scrollbar bugs.", id_map),
        todo_item("Answered Active Recall questions and recorded personal notes in Section 5.", id_map),
        todo_item("Updated `Status` and `Mastery (0-4)` properties on this page.", id_map),
    ]

def build_prg_t00_c01_u07(id_map):
    return [
        callout_block(
            "**Learning Objective:** Engineer accessible web interfaces conforming to WCAG 2.1 AA standards: high-contrast color ratios (4.5:1), visible keyboard focus rings (`:focus-visible`), logical tab order (`tabindex`), and ARIA landmarks.\n"
            "**Expected Output:** Navigate and operate any web page using only the keyboard (`Tab`, `Shift+Tab`, `Enter`, `Space`, `Esc`), audit accessibility trees, and achieve 100% Lighthouse Accessibility scores.\n"
            "**Parent:** [[PRG-T00]] → [[PRG-T00-C01]] | **Prerequisites:** [[PRG-T00-C01-U02]] | **Next Unit:** [[PRG-T00-C01-U08]] | **Source:** [[R033]] (`Web.dev Accessibility`)",
            id_map,
            color="blue_background",
        ),
        h2("1. Core Concepts & Architectural Mental Model", id_map),
        bullet("**1. The 4 Principles of WCAG (POUR):**", id_map, children=[
            bullet("**Perceivable:** Information must be presentable to users in ways they can perceive (text alternatives, minimum 4.5:1 contrast for normal text, 3:1 for large text/icons).", id_map),
            bullet("**Operable:** Interface components must be fully navigable and operable via keyboard alone.", id_map),
            bullet("**Understandable:** Information and operation of UI must be intuitive and consistent.", id_map),
            bullet("**Robust:** Content must be reliably interpreted across assistive technologies (screen readers like VoiceOver/NVDA).", id_map),
        ]),
        bullet("**2. Keyboard Navigation & Visible Focus Rings:**", id_map, children=[
            bullet("All interactive elements (`<a>`, `<button>`, `<input>`, `<select>`) must receive keyboard focus via `Tab`.", id_map),
            bullet("Never hide focus outlines globally with `outline: none`. Use `:focus-visible` to present crisp high-contrast outlines for keyboard users while preserving clean visuals for mouse clicks.", id_map),
            bullet("Use `tabindex=\"0\"` to make a non-interactive element focusable in document order. Use `tabindex=\"-1\"` for programmatic focus via JS (`element.focus()`). **Never use positive `tabindex` (`tabindex=\"1\"`)** as it breaks logical tab sequence.", id_map),
        ]),
        divider_block(),
        h2("2. Code & Structure Examples", id_map),
        h3("Example 1: High-Contrast Accessible Focus Rings and Skip-Navigation Link", id_map),
        code_block(
            "/* 1. Accessible Skip Navigation Link */\n"
            ".skip-link {\n"
            "  position: absolute;\n"
            "  top: -100px;\n"
            "  left: 1rem;\n"
            "  padding: 0.75rem 1.5rem;\n"
            "  background: #0f172a;\n"
            "  color: #ffffff;\n"
            "  z-index: 1000;\n"
            "  border-radius: 4px;\n"
            "  transition: top 0.2s;\n"
            "}\n"
            ".skip-link:focus {\n"
            "  top: 1rem;\n"
            "}\n\n"
            "/* 2. Accessible Focus Indicator (:focus-visible) */\n"
            "button:focus-visible,\n"
            "a:focus-visible,\n"
            "input:focus-visible {\n"
            "  outline: 3px solid #2563eb;\n"
            "  outline-offset: 2px;\n"
            "}\n\n"
            "/* Remove focus ring for mouse users while preserving keyboard visibility */\n"
            "button:focus:not(:focus-visible) {\n"
            "  outline: none;\n"
            "}",
            "css",
        ),
        divider_block(),
        h2("3. Practice Guide", id_map),
        p_block("Use this blueprint to drill accessibility audits and keyboard operability:", id_map),
        bullet("**1. Core Skills to Drill:**", id_map, children=[
            bullet("**No-Mouse Navigation Test:** Unplug your mouse; navigate your entire application using only `Tab`, `Shift+Tab`, `Space`, and `Enter`. Ensure every link, button, and input is reachable and clearly highlighted.", id_map),
            bullet("**VoiceOver / NVDA Screen Reader Audit:** Turn on macOS VoiceOver (`Cmd + F5`) or Windows NVDA; verify that form inputs announce their associated labels and landmark regions announce correctly.", id_map),
        ]),
        bullet("**2. Combine with Prior Units:**", id_map, children=[
            bullet("**Bridge to [[PRG-T00-C01-U02]]:** Native HTML5 elements give 90% of accessibility for free without writing custom ARIA.", id_map),
        ]),
        bullet("**3. Common Traps & Edge Cases to Test:**", id_map, children=[
            bullet("**Positive Tabindex Anti-Pattern:** Setting `tabindex=\"2\"` forces that element ahead of the entire page tab order, causing jarring jumps.", id_map),
            bullet("**Low Contrast Placeholder Trap:** Using faint gray text (`#cbd5e1` on white) for placeholders that fails the 4.5:1 WCAG contrast ratio.", id_map),
        ]),
        bullet("**4. Cross-Subject & Real-World Connection (React / Next.js):**", id_map, children=[
            bullet("**Bridge to [[PRG-T02]] (Radix UI / Shadcn):** Modern UI libraries build on top of unstyled accessible primitives that enforce keyboard focus traps in dialogs and dropdowns.", id_map),
        ]),
        divider_block(),
        h2("4. Active Recall Questions", id_map),
        toggle_block(
            "1. What is the difference between `:focus` and `:focus-visible`?",
            [
                "`:focus` triggers whenever an element receives focus by any means, including mouse clicks, touch taps, or keyboard navigation. `:focus-visible` selectively triggers only when the browser determines that focus should be visually evident—most notably during keyboard navigation (`Tab`) or when an input requires typing.",
            ],
            id_map,
        ),
        toggle_block(
            "2. What is the golden rule of ARIA (Accessible Rich Internet Applications)?",
            [
                "The first rule of ARIA is: 'If you can use a native HTML element or attribute with the semantics and behavior you require already built in, then do so instead of re-purposing an element and adding ARIA roles.' Native elements (`<button>`, `<dialog>`, `<nav>`) are far more reliable than custom ARIA implementations."
            ],
            id_map,
        ),
        divider_block(),
        h2("5. My Implementation & Mistake Log", id_map),
        quote_block("**Feynman One-Liner (Summarize Accessibility in your own words):**\n[Write your summary here after studying]", id_map),
        quote_block("**My Solution / Working / Code (Focus ring styles, keyboard navigation tests):**\n[Paste your a11y experiments here]", id_map),
        quote_block("**Mistake & Pitfall Log (Record keyboard focus issues or contrast failures):**\n- [Log mistakes and lessons learned here]", id_map),
        divider_block(),
        h2("6. Completion Checklist & Mastery Review", id_map),
        todo_item("Navigated the entire application successfully using only keyboard Tab/Enter.", id_map),
        todo_item("Verified text contrast ratios meet WCAG 2.1 AA (>= 4.5:1).", id_map),
        todo_item("Answered Active Recall questions and recorded personal notes in Section 5.", id_map),
        todo_item("Updated `Status` and `Mastery (0-4)` properties on this page.", id_map),
    ]

def build_prg_t00_c01_u08(id_map):
    return [
        callout_block(
            "**Learning Objective:** Master Chrome DevTools for diagnostic debugging: DOM/CSSOM tree inspection, computed styles, Network waterfall timing analysis (TTFB, payload size, caching), Console debugging, and automated Lighthouse audits.\n"
            "**Expected Output:** Diagnose frontend visual bugs, network latency bottlenecks, and accessibility flaws using DevTools panels without resorting to blind guessing.\n"
            "**Parent:** [[PRG-T00]] → [[PRG-T00-C01]] | **Prerequisites:** [[PRG-T00-C01-U01]] through [[PRG-T00-C01-U07]] | **Sources:** [[R001]], [[R002]], [[R030]], [[R032]] (`Web.dev Performance`)",
            id_map,
            color="blue_background",
        ),
        h2("1. Core Concepts & Architectural Mental Model", id_map),
        bullet("**1. Essential DevTools Panels & Capabilities:**", id_map, children=[
            bullet("**Elements Panel:** Live DOM tree inspection, computed CSS styles, box model visualization, and DOM breakpoint debugging (break on subtree modifications).", id_map),
            bullet("**Console Panel:** Runtime JavaScript REPL, interactive element selection (`$0` for currently inspected node, `$$('selector')` for `querySelectorAll`), and logging levels (`console.warn`, `console.error`, `console.table`).", id_map),
            bullet("**Network Panel:** Real-time request inspection, filter by resource type (Fetch/XHR, JS, CSS, Img), disable cache, network throttling (Slow 3G, Offline), and waterfall timing inspection.", id_map),
            bullet("**Application Panel:** Inspect client-side storage: Cookies, `localStorage`, `sessionStorage`, IndexedDB, and Cache Storage.", id_map),
            bullet("**Lighthouse Panel:** Automated auditing across 5 categories: Performance, Accessibility, Best Practices, SEO, and PWA.", id_map),
        ]),
        divider_block(),
        h2("2. Code & Structure Examples", id_map),
        h3("Example 1: DevTools Console Power Tricks for Rapid Debugging", id_map),
        code_block(
            "// In Chrome DevTools Console:\n"
            "// 1. Inspect the currently selected element in the Elements panel:\n"
            "console.dir($0);\n\n"
            "// 2. Query all matching elements as a real Array:\n"
            "const navLinks = $$('nav a');\n"
            "console.table(navLinks.map(a => ({ text: a.textContent, href: a.href })));\n\n"
            "// 3. Monitor function calls and execution timing:\n"
            "console.time('renderList');\n"
            "// ... execute operation ...\n"
            "console.timeEnd('renderList'); // Output: renderList: 4.12ms",
            "javascript",
        ),
        divider_block(),
        h2("3. Practice Guide", id_map),
        p_block("Use this blueprint to drill professional DevTools debugging and performance profiling:", id_map),
        bullet("**1. Core Skills to Drill:**", id_map, children=[
            bullet("**Network Waterfall Diagnosis:** Identify blocking resources, compare Gzip vs Brotli transfer sizes, and verify 304 Not Modified cache hits.", id_map),
            bullet("**Lighthouse Performance Audit:** Run an audit on a local web page, identify Largest Contentful Paint (LCP) and Cumulative Layout Shift (CLS) issues, and remediate them to 95+ score.", id_map),
        ]),
        bullet("**2. Combine with Prior Units:**", id_map, children=[
            bullet("**Bridge to [[PRG-T00-C01-U01]]:** Verify DNS lookup and SSL handshake phases directly in the Network timing bar.", id_map),
            bullet("**Bridge to [[PRG-T00-C01-U04]]:** Use the Box Model diagram in Computed Styles to spot padding/border miscalculations.", id_map),
        ]),
        bullet("**3. Common Traps & Edge Cases to Test:**", id_map, children=[
            bullet("**Testing With Cache Enabled:** Debugging stale CSS because 'Disable cache' is unchecked in the Network tab while DevTools is open.", id_map),
            bullet("**Ignoring Mobile Throttling:** Assuming your site is fast because it runs on localhost with zero latency. Always profile under 'Fast 3G' or 'Slow 3G'.", id_map),
        ]),
        bullet("**4. Cross-Subject & Real-World Connection (Next.js Profiling):**", id_map, children=[
            bullet("**Bridge to [[PRG-T03]]:** DevTools Network waterfall inspection is the primary tool used to measure Next.js Server-Side Rendering (SSR) Time to First Byte and Client Hydration timing.", id_map),
        ]),
        divider_block(),
        h2("4. Active Recall Questions", id_map),
        toggle_block(
            "1. What is the difference between 'Size' and 'Resource' in the DevTools Network tab?",
            [
                "'Size' represents the actual number of compressed bytes transferred over the network (including HTTP headers and Gzip/Brotli compression). 'Resource' represents the uncompressed, decoded size of the asset once decompressed in memory. A large difference indicates effective compression."
            ],
            id_map,
        ),
        toggle_block(
            "2. How does checking 'Disable cache' in DevTools assist frontend debugging?",
            [
                "Browsers aggressively cache CSS, JavaScript, and static assets according to HTTP `Cache-Control` headers. Checking 'Disable cache' ensures that every page reload fetches fresh assets from the server while DevTools is open, preventing you from debugging phantom issues caused by stale cached scripts."
            ],
            id_map,
        ),
        divider_block(),
        h2("5. My Implementation & Mistake Log", id_map),
        quote_block("**Feynman One-Liner (Summarize DevTools capabilities in your own words):**\n[Write your summary here after studying]", id_map),
        quote_block("**My Solution / Working / Code (Lighthouse audit scores, network waterfall screenshots/notes):**\n[Paste your DevTools findings here]", id_map),
        quote_block("**Mistake & Pitfall Log (Record DevTools misconceptions or profiling traps):**\n- [Log mistakes and lessons learned here]", id_map),
        divider_block(),
        h2("6. Completion Checklist & Mastery Review", id_map),
        todo_item("Used Elements, Console, Network, and Application panels in Chrome DevTools.", id_map),
        todo_item("Executed a Lighthouse audit and resolved all accessibility/performance warnings.", id_map),
        todo_item("Answered Active Recall questions and recorded personal notes in Section 5.", id_map),
        todo_item("Updated `Status` and `Mastery (0-4)` properties on this page.", id_map),
    ]

def run_upgrade():
    env = load_env()
    token = env.get("NOTION_TOKEN")
    if not token:
        raise RuntimeError("NOTION_TOKEN not set")

    with open("id_map.json", "r", encoding="utf-8") as f:
        id_map = json.load(f)

    # 1. Topic: PRG-T00
    print("=== Upgrading PRG-T00 Topic ===")
    t_blocks = build_prg_t00_topic(id_map)
    validate_blocks_clean(t_blocks, "PRG-T00")
    replace_page_blocks(id_map["PRG-T00"]["id"], t_blocks, "PRG-T00", token)

    # 2. Chapter: PRG-T00-C01
    print("=== Upgrading PRG-T00-C01 Chapter ===")
    c_blocks = build_prg_t00_c01(id_map)
    validate_blocks_clean(c_blocks, "PRG-T00-C01")
    replace_page_blocks(id_map["PRG-T00-C01"]["id"], c_blocks, "PRG-T00-C01", token)

    # 3. Units: PRG-T00-C01-U01 through U08
    unit_builders = [
        ("PRG-T00-C01-U01", build_prg_t00_c01_u01),
        ("PRG-T00-C01-U02", build_prg_t00_c01_u02),
        ("PRG-T00-C01-U03", build_prg_t00_c01_u03),
        ("PRG-T00-C01-U04", build_prg_t00_c01_u04),
        ("PRG-T00-C01-U05", build_prg_t00_c01_u05),
        ("PRG-T00-C01-U06", build_prg_t00_c01_u06),
        ("PRG-T00-C01-U07", build_prg_t00_c01_u07),
        ("PRG-T00-C01-U08", build_prg_t00_c01_u08),
    ]

    for uid, builder_fn in unit_builders:
        print(f"=== Upgrading Unit: {uid} ===")
        u_blocks = builder_fn(id_map)
        validate_blocks_clean(u_blocks, uid)
        replace_page_blocks(id_map[uid]["id"], u_blocks, uid, token)

    print("\n🎉 SUCCESS! PRG-T00 Topic, Chapter C01, and all 8 Units upgraded to v3 Gold Standard!")

if __name__ == "__main__":
    run_upgrade()
