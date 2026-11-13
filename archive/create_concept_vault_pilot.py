# -*- coding: utf-8 -*-
"""
Script to populate the Concept Vault database in Notion with 5 pilot concepts:
1. DNS (Domain Name System)
2. TCP 3-Way Handshake
3. TLS & Modern Encryption
4. HTTP Protocol Anatomy
5. WebSocket Protocol

Follows the concise, 60-second recovery structure requested by the user:
- What is it? (Definition in plain words)
- Real-world Analogy & Mental Model
- How it works & Concrete Example
- Comparison Table / Matrix
- Common Traps & Failure Modes
"""
import json
import time
from apply_rules_and_test_pages import (
    load_env,
    notion_request,
    h2,
    h3,
    p_block,
    callout_block,
    quote_block,
    bullet,
    num_item,
    code_block,
    divider_block,
    replace_page_blocks,
    validate_blocks_clean,
    get_all_blocks,
)

CONCEPT_DB_ID = "4103818f-8ba0-8164-aa0d-eeb2d6cb65b0"

def get_dns_blocks(id_map):
    return [
        callout_block(
            "**TL;DR in 1 Sentence:** The Internet's phonebook translating human-friendly domain names (`google.com`) into machine-routable IP addresses (`142.250.190.46`).\n"
            "**Domain:** Networking | **Used in:** [[PRG-T00-C01-U01]]",
            id_map,
            color="blue_background",
        ),
        h2("1. What Is It? (Core Definition)", id_map),
        p_block(
            "DNS (Domain Name System) is a globally distributed, hierarchical database system. Computers routing network packets across the Internet communicate exclusively via numerical IP addresses (IPv4 / IPv6). Humans remember alphanumeric names. DNS bridges this gap without a single point of failure.",
            id_map,
        ),
        divider_block(),
        h2("2. Real-World Analogy & Mental Model", id_map),
        bullet("**The Smartphone Contacts List:**", id_map, children=[
            bullet("When you want to call Mom, you tap 'Mom' on your screen, not `+66-81-234-5678`. Your phone looks up 'Mom' in its local address book to find the real number.", id_map),
            bullet("If you don't have the number, you call Directory Assistance (DNS Recursive Resolver), which looks it up across telecom registries until it finds the exact house number.", id_map),
        ]),
        divider_block(),
        h2("3. How It Works (Step-by-Step)", id_map),
        num_item("1. **Browser Cache Check:** Browser checks if it recently resolved `example.com`.", id_map),
        num_item("2. **OS & Hosts Cache:** OS checks local `/etc/hosts` and operating system DNS resolver cache.", id_map),
        num_item("3. **Recursive Resolver (ISP / 8.8.8.8):** Queries on your behalf if un-cached.", id_map),
        num_item("4. **Root Nameservers (`.`):** Directs the query to the Top-Level Domain (TLD) server.", id_map),
        num_item("5. **TLD Nameservers (`.com`):** Directs the query to the Authoritative server for `example.com`.", id_map),
        num_item("6. **Authoritative Nameserver:** Returns the definitive record (e.g. `A 93.184.216.34`).", id_map),
        code_block(
            "# Practical Command to trace DNS lookup step-by-step:\n"
            "dig example.com +trace\n"
            "\n"
            "# Quick lookup:\n"
            "nslookup example.com",
            "shell",
        ),
        divider_block(),
        h2("4. Comparison: Local Hosts vs. Global DNS", id_map),
        bullet("**`/etc/hosts` File:** Static text file on your local machine. Takes precedence over DNS. Used for local development (e.g., mapping `localhost` to `127.0.0.1`).", id_map),
        bullet("**Global DNS:** Distributed worldwide across thousands of servers with caching, load balancing, and failover.", id_map),
        divider_block(),
        h2("5. Common Gotchas & Traps", id_map),
        bullet("⚠️ **Stale TTL (Time-To-Live) Nightmare:** When migrating servers, if your DNS TTL was set to 86400 (24 hours), old users will keep connecting to the decommissioned server for up to 24 hours. *Best Practice: Lower TTL to 300s (5 minutes) before migration.*", id_map),
        bullet("⚠️ **DNS Propagation is a Myth:** DNS does not 'propagate' like waves; it is pure caching. Once cache expires based on TTL, the next query hits the fresh authoritative server.", id_map),
    ]

def get_tcp_blocks(id_map):
    return [
        callout_block(
            "**TL;DR in 1 Sentence:** A reliable, 3-step greeting handshake (`SYN` -> `SYN-ACK` -> `ACK`) that verifies both client and server can hear and talk before sending actual data.\n"
            "**Domain:** Networking | **Used in:** [[PRG-T00-C01-U01]]",
            id_map,
            color="blue_background",
        ),
        h2("1. What Is It? (Core Definition)", id_map),
        p_block(
            "Transmission Control Protocol (TCP) is a connection-oriented transport protocol. Because the underlying IP network can drop, duplicate, or reorder packets, TCP establishes a virtual connection using a 3-way handshake to agree on initial Sequence Numbers (ISN) and buffer capacities.",
            id_map,
        ),
        divider_block(),
        h2("2. Real-World Analogy & Mental Model", id_map),
        bullet("**The Two-Way Radio Check:**", id_map, children=[
            bullet("1. **SYN (Synchronize):** Client says, *'Radio check, can you hear me?'*", id_map),
            bullet("2. **SYN-ACK (Sync-Acknowledge):** Server says, *'Loud and clear! Can you hear me?'*", id_map),
            bullet("3. **ACK (Acknowledge):** Client says, *'Got you loud and clear too. Ready, sending message now!'*", id_map),
        ]),
        divider_block(),
        h2("3. How It Works (Protocol Exchange)", id_map),
        code_block(
            "CLIENT                               SERVER\n"
            "  │                                    │\n"
            "  ├──── [1] SYN (seq = 100) ──────────>│ (Server allocates buffer)\n"
            "  │                                    │\n"
            "  │<─── [2] SYN-ACK (seq=300,ack=101) ─┤\n"
            "  │                                    │\n"
            "  ├──── [3] ACK (ack = 301) ──────────>│ (Connection ESTABLISHED!)\n"
            "  │                                    │\n"
            "  └──── HTTP GET Request Data travels ─┘",
            "plain text",
        ),
        divider_block(),
        h2("4. Comparison: TCP vs. UDP", id_map),
        bullet("**TCP (Reliable):** Handshake required (1 RTT latency overhead). Retransmits lost packets. Guarantees in-order delivery. Used for Web (HTTP/1, HTTP/2), Email, File transfers.", id_map),
        bullet("**UDP (Fast):** Connectionless, zero handshake. Drops lost packets without retransmission. Used for Live Video Streaming, Multiplayer Gaming, DNS queries, and HTTP/3 (QUIC).", id_map),
        divider_block(),
        h2("5. Common Gotchas & Traps", id_map),
        bullet("⚠️ **The Latency Tax (1 RTT):** Creating a new TCP connection requires 1 full Round-Trip Time before any HTTP request can be sent. On high-latency mobile networks (100ms RTT), this adds 100ms of pure waiting.", id_map),
        bullet("⚠️ **Solution:** Always use HTTP Keep-Alive (`Connection: keep-alive`) or HTTP/2 multiplexing to reuse existing TCP connections instead of opening a fresh handshake per asset.", id_map),
    ]

def get_tls_blocks(id_map):
    return [
        callout_block(
            "**TL;DR in 1 Sentence:** The security layer transforming plain HTTP into encrypted HTTPS using digital certificates to verify identity and secret keys to lock data.\n"
            "**Domain:** Security | **Used in:** [[PRG-T00-C01-U01]]",
            id_map,
            color="red_background",
        ),
        h2("1. What Is It? (Core Definition)", id_map),
        p_block(
            "Transport Layer Security (TLS 1.3) operates directly on top of TCP. It guarantees three fundamental security properties: **Authentication** (proves you are talking to the real bank, not an impostor), **Confidentiality** (encrypts messages so ISP/hackers cannot read), and **Integrity** (detects if any bytes were altered).",
            id_map,
        ),
        divider_block(),
        h2("2. Real-World Analogy & Mental Model", id_map),
        bullet("**The Armored Glass Lockbox:**", id_map, children=[
            bullet("**Certificate = Passport/Badge:** The server shows a digitally notarized badge signed by a trusted government authority (Certificate Authority / CA) proving its identity.", id_map),
            bullet("**Asymmetric Encryption:** You use the server's public lock to send a secret combination code that only the server's private key can open.", id_map),
            bullet("**Symmetric Encryption:** Once both have that combination code, they lock and unlock messages instantly with blazing fast speed.", id_map),
        ]),
        divider_block(),
        h2("3. How It Works (TLS 1.3 1-RTT Flow)", id_map),
        num_item("1. **Client Hello:** Client sends supported cipher suites and ephemeral public key share.", id_map),
        num_item("2. **Server Hello & Certificate:** Server replies with its key share, verified digital certificate, and TLS handshake finished.", id_map),
        num_item("3. **Symmetric Session Key Derived:** Both parties calculate identical AES-GCM or ChaCha20 encryption keys independently in memory.", id_map),
        num_item("4. **Encrypted Application Data:** All HTTP headers and body travel in uncrackable cipher text.", id_map),
        code_block(
            "# Inspect TLS handshake details from terminal:\n"
            "curl -vI https://google.com\n"
            "# Look for: * TLSv1.3 (IN), TLS handshake, Finished",
            "shell",
        ),
        divider_block(),
        h2("4. Comparison: Asymmetric vs. Symmetric Encryption", id_map),
        bullet("**Asymmetric (Public + Private Key):** Used ONLY during the initial handshake. Mathematically expensive. Solves key distribution problem.", id_map),
        bullet("**Symmetric (Single Shared Session Key):** Used for 100% of data transmission. Extremely fast (hardware-accelerated by modern CPU instructions).", id_map),
        divider_block(),
        h2("5. Common Gotchas & Traps", id_map),
        bullet("⚠️ **Expired SSL Certificate:** If a site's SSL cert expires, browsers display catastrophic red warning screens ('Your connection is not private'), instantly killing user trust and traffic.", id_map),
        bullet("⚠️ **Mixed Content Bug:** Loading an `http://` script or image inside an `https://` page causes browsers to block the resource completely for security reasons.", id_map),
    ]

def get_http_blocks(id_map):
    return [
        callout_block(
            "**TL;DR in 1 Sentence:** The stateless, text-based request-response protocol of the web where clients ask for resources via Methods and servers answer with Status Codes.\n"
            "**Domain:** Web Platform | **Used in:** [[PRG-T00-C01-U01]]",
            id_map,
            color="green_background",
        ),
        h2("1. What Is It? (Core Definition)", id_map),
        p_block(
            "Hypertext Transfer Protocol (HTTP) is the application-level protocol governing client-server communication. A client sends an explicit HTTP Request message; the server executes logic and returns an HTTP Response message. HTTP is inherently stateless—each transaction is independent unless tracked by cookies or tokens.",
            id_map,
        ),
        divider_block(),
        h2("2. Real-World Analogy & Mental Model", id_map),
        bullet("**The Restaurant Order Slip:**", id_map, children=[
            bullet("**Request:** You fill out an order slip with Method (`GET /pasta`), Table ID (`Host`), and Dietary restrictions (`Headers: Accept: gluten-free`).", id_map),
            bullet("**Response:** Chef returns the plate (`Body`) along with a Status Bill: `200 OK` (Enjoy your meal), `404 Not Found` (Out of pasta), or `500 Server Error` (Kitchen stove caught fire).", id_map),
        ]),
        divider_block(),
        h2("3. Wire Protocol Anatomy (Raw Format)", id_map),
        code_block(
            "// 1. REQUEST STRUCTURE\n"
            "GET /api/v1/users/42 HTTP/1.1         <-- Request Line (Method + Path + Version)\n"
            "Host: api.example.com                 <-- Target Host Header\n"
            "Authorization: Bearer secret_token... <-- Auth Header\n"
            "Accept: application/json              <-- Desired response format\n"
            "\n"
            "// 2. RESPONSE STRUCTURE\n"
            "HTTP/1.1 200 OK                       <-- Status Line (Version + Code + Phrase)\n"
            "Content-Type: application/json        <-- Payload MIME type\n"
            "Content-Length: 45                    <-- Body byte count\n"
            "\n"
            "{\"id\": 42, \"name\": \"Joseph\", \"role\": \"admin\"}  <-- Response Body",
            "plain text",
        ),
        divider_block(),
        h2("4. Comparison: HTTP Methods Matrix", id_map),
        bullet("`GET` — Read data only. Must be **safe** and **idempotent** (calling 100 times has no side effects). No request body.", id_map),
        bullet("`POST` — Create new resource or process data. **Not idempotent** (calling 10 times creates 10 records). Carries body.", id_map),
        bullet("`PUT` — Replace resource entirely. **Idempotent** (replacing with identical payload produces same state).", id_map),
        bullet("`PATCH` — Partial update (e.g. updating only user email).", id_map),
        bullet("`DELETE` — Remove resource. **Idempotent**.", id_map),
        divider_block(),
        h2("5. Common Gotchas & Traps", id_map),
        bullet("⚠️ **401 Unauthorized vs. 403 Forbidden:** `401` means unauthenticated (You have not logged in or token is expired). `403` means authenticated but unauthorized (You logged in as Normal User, but this endpoint requires Admin role).", id_map),
        bullet("⚠️ **502 vs. 504 Gateway Error:** `502 Bad Gateway` means the upstream server crashed or gave garbled data. `504 Gateway Timeout` means the upstream server took too long to respond before the proxy timer expired.", id_map),
    ]

def get_websocket_blocks(id_map):
    return [
        callout_block(
            "**TL;DR in 1 Sentence:** A persistent, two-way open pipeline over a single connection where both client and server can send messages to each other at any millisecond.\n"
            "**Domain:** Web Platform | **Used in:** [[PRG-T00-C01-U01]]",
            id_map,
            color="orange_background",
        ),
        h2("1. What Is It? (Core Definition)", id_map),
        p_block(
            "WebSocket is a full-duplex, bidirectional communication protocol standardized under RFC 6455. Unlike traditional HTTP where the client must initiate every request and wait for a response, WebSocket maintains an open TCP socket allowing real-time, low-overhead frame exchange.",
            id_map,
        ),
        divider_block(),
        h2("2. Real-World Analogy & Mental Model", id_map),
        bullet("**Walkie-Talkie Polling vs. Open Telephone Call:**", id_map, children=[
            bullet("**HTTP Short/Long Polling:** Calling someone every 2 seconds: *'Any new mail? No.'* -> *'Any new mail? No.'* Wasteful and laggy.", id_map),
            bullet("**WebSocket:** A live open phone call. The moment either party has something to say, they speak immediately without redialing or re-introducing themselves.", id_map),
        ]),
        divider_block(),
        h2("3. How It Works (The HTTP Upgrade Handshake)", id_map),
        p_block(
            "WebSocket begins its life as a standard HTTP request with special upgrade headers. Once accepted with status `101 Switching Protocols`, HTTP steps aside and the connection switches to raw WebSocket framing.",
            id_map,
        ),
        code_block(
            "// Client initiates handshake:\n"
            "GET /chat HTTP/1.1\n"
            "Host: live.example.com\n"
            "Upgrade: websocket\n"
            "Connection: Upgrade\n"
            "Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==\n"
            "\n"
            "// Server accepts handshake:\n"
            "HTTP/1.1 101 Switching Protocols\n"
            "Upgrade: websocket\n"
            "Connection: Upgrade\n"
            "Sec-WebSocket-Accept: s3pPLMBiTxaQ9kYGzzhZRbK+xOo=",
            "plain text",
        ),
        code_block(
            "// Simple JavaScript browser API:\n"
            "const socket = new WebSocket('wss://live.example.com/chat');\n"
            "\n"
            "socket.addEventListener('open', () => {\n"
            "  socket.send(JSON.stringify({ text: 'Hello, room!' }));\n"
            "});\n"
            "\n"
            "socket.addEventListener('message', (event) => {\n"
            "  console.log('Live message from server:', event.data);\n"
            "});",
            "javascript",
        ),
        divider_block(),
        h2("4. Comparison: HTTP vs. WebSocket vs. SSE", id_map),
        bullet("**Standard HTTP:** Unidirectional (Client pulls). High header overhead (1KB per request). Perfect for standard REST APIs, websites, file downloads.", id_map),
        bullet("**Server-Sent Events (SSE):** Unidirectional (Server pushes down to client). Simple HTTP streaming. Great for live stock tickers, notification feeds.", id_map),
        bullet("**WebSocket:** Full-Duplex (Both directions simultaneously). Tiny frame overhead (2 to 10 bytes). Indispensable for multiplayer gaming, live chat apps, collaborative document editing.", id_map),
        divider_block(),
        h2("5. Common Gotchas & Traps", id_map),
        bullet("⚠️ **Stateful Connection Burden:** HTTP servers are stateless and easily auto-scale behind standard load balancers. WebSockets are stateful (the socket lives on one specific server memory instance). Scaling requires Redis Pub/Sub backplanes.", id_map),
        bullet("⚠️ **The Thundering Herd Disconnect:** If a server restarts, 50,000 active WebSocket clients disconnect and attempt to reconnect in the exact same second, crashing the incoming gateway unless exponential backoff jitter is implemented.", id_map),
    ]

PILOT_CONCEPTS = [
    {
        "key": "CON-DNS",
        "name": "DNS (Domain Name System)",
        "domain": "Networking",
        "summary": "The Internet's phonebook translating human domain names to machine IP addresses.",
        "blocks_builder": get_dns_blocks,
    },
    {
        "key": "CON-TCP-HANDSHAKE",
        "name": "TCP 3-Way Handshake",
        "domain": "Networking",
        "summary": "The SYN -> SYN-ACK -> ACK connection protocol ensuring reliable, two-way packet streams.",
        "blocks_builder": get_tcp_blocks,
    },
    {
        "key": "CON-TLS",
        "name": "TLS & Modern Encryption",
        "domain": "Security",
        "summary": "Cryptographic security layer authenticating servers and encrypting web traffic into HTTPS.",
        "blocks_builder": get_tls_blocks,
    },
    {
        "key": "CON-HTTP",
        "name": "HTTP Protocol Anatomy",
        "domain": "Web Platform",
        "summary": "Stateless application request-response protocol powering the World Wide Web.",
        "blocks_builder": get_http_blocks,
    },
    {
        "key": "CON-WEBSOCKET",
        "name": "WebSocket Protocol",
        "domain": "Web Platform",
        "summary": "Persistent, full-duplex bidirectional communication channel over a single TCP connection.",
        "blocks_builder": get_websocket_blocks,
    },
]

def main():
    env = load_env(".env")
    token = env["NOTION_TOKEN"]

    with open("id_map.json") as f:
        id_map = json.load(f)

    # 1. Register Database in id_map
    id_map["CONCEPT_VAULT_DB"] = {
        "id": CONCEPT_DB_ID,
        "title": "Concept Vault"
    }

    print(f"--- CREATING 5 PILOT CONCEPT NOTES IN DATABASE {CONCEPT_DB_ID} ---")
    created_pages = {}

    for item in PILOT_CONCEPTS:
        key = item["key"]
        name = item["name"]
        domain = item["domain"]
        summary = item["summary"]

        print(f"Creating page for {name} ({key})...", end="", flush=True)

        # Check if already exists in id_map to avoid duplicating
        existing_id = id_map.get(key, {}).get("id") if isinstance(id_map.get(key), dict) else None

        if not existing_id:
            # Create Page in Notion
            page_payload = {
                "parent": {"database_id": CONCEPT_DB_ID},
                "properties": {
                    "Name": {"title": [{"text": {"content": name}}]},
                    "Domain": {"select": {"name": domain}},
                    "Summary": {"rich_text": [{"text": {"content": summary}}]},
                }
            }
            res = notion_request("POST", "pages", token, page_payload)
            page_id = res["id"]
            id_map[key] = {"id": page_id, "title": name}
            print(f" Created page ID: {page_id}")
        else:
            page_id = existing_id
            print(f" Reusing existing ID: {page_id}")

        created_pages[key] = page_id

    # Save id_map with new Concept keys
    with open("id_map.json", "w") as f:
        json.dump(id_map, f, indent=2, ensure_ascii=False)
    print("✓ Saved updated id_map.json with new Concept IDs.")

    # 2. Populate Blocks for each Concept Page
    print("\n--- POPULATING CONTENT BLOCKS ---")
    for item in PILOT_CONCEPTS:
        key = item["key"]
        name = item["name"]
        page_id = created_pages[key]
        blocks_fn = item["blocks_builder"]

        blocks = blocks_fn(id_map)
        validate_blocks_clean(blocks, label=key)
        print(f"Updating blocks for {key} ({len(blocks)} blocks)...", end="", flush=True)
        replace_page_blocks(page_id, blocks, key, token)
        print(" DONE")
        time.sleep(0.3)

    print("\n🎉 All 5 Concept Notes created and populated successfully in Notion!")

if __name__ == "__main__":
    main()
