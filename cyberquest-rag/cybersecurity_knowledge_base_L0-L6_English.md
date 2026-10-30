# Cybersecurity Knowledge Base (Combined L0–L6)

> This document was created by combining the L0–L6 Markdown files from `cybersecurity_knowledge_base.zip`.

> The original body content is preserved and arranged from L0 to L6. Each level is marked with a section heading.

## Table of Contents

1. [L0 — Security Awareness and Professional Ethics](#l0--security-awareness-and-professional-ethics)
2. [L1 — Computer and Operating System Fundamentals](#l1--computer-and-operating-system-fundamentals)
3. [L2 — Networking Principles and Basic Tools](#l2--networking-principles-and-basic-tools)
4. [L3 — Core Cybersecurity Principles](#l3--core-cybersecurity-principles)
5. [L4 — Common Security Issues and Defensive Practices](#l4--common-security-issues-and-defensive-practices)
6. [L5 — Core Knowledge for Cybersecurity Specialisations](#l5--core-knowledge-for-cybersecurity-specialisations)
7. [L6 — Advanced Security Engineering and Research](#l6--advanced-security-engineering-and-research)

---

<a id="l0--security-awareness-and-professional-ethics"></a>

# L0 — Security Awareness and Professional Ethics

# L0 | Security Awareness and Professional Ethics: Core Knowledge

## K0-001 | Definition of Cybersecurity
Cybersecurity uses technology, processes, and people management to protect systems, networks, applications, and data from unauthorised access, damage, disclosure, tampering, or disruption. Cybersecurity is not just about installing antivirus software; it also includes identity management, system updates, risk management, monitoring, incident response, business recovery, and staff training.

Cybersecurity objectives are commonly described by the CIA triad:
- **Confidentiality:** Only authorised parties can access information.
- **Integrity:** Information and systems are not changed or damaged without authorisation.
- **Availability:** Authorised users can use systems and data when they need them.

For example, an unauthorised person reading customer records is a confidentiality issue; a payment amount being altered is an integrity issue; and ransomware making business systems unusable is an availability issue. One incident may affect all three objectives.

## K0-002 | Assets, Threats, Vulnerabilities, and Risk
- **Asset:** Something that needs protection, such as an account, laptop, database, business service, or intellectual property.
- **Threat:** An actor, event, or condition that could cause harm, such as a phishing attack, lost device, or power outage.
- **Vulnerability:** A weakness in a system, process, or configuration, such as unpatched software, overly broad access permissions, or missing backups.
- **Risk:** An overall judgement of the likelihood that a threat will exploit a weakness and the consequences that may result.

Example: a customer database is an asset; account compromise is a threat scenario; the absence of multi-factor authentication is a weakness; and unauthorised access to customer records and its business consequences constitute risk. Risk assessment is not simply a matter of treating the “number of vulnerabilities” as a measure of risk. It should also consider exposure, exploitability, asset importance, existing controls, and potential impact.

## K0-003 | Phishing and Social Engineering
Phishing attacks impersonate trusted organisations or people to persuade victims to click links, open attachments, disclose credentials, or make payments. Social engineering exploits trust, urgency, authority, curiosity, or fear to influence people's judgement.

Common warning signs include an unusual sender domain, an unexpected attachment, a request for a password or verification code, a request to bypass normal procedures, a sudden change to payment details, or a threat to disable an account immediately. A single sign does not by itself prove that a message is malicious. Verify the sender and request through an independent channel.

A safe response process:
1. Do not click suspicious links or open unknown attachments.
2. Do not verify the message using contact details supplied in the email. Use a known official phone number or address instead.
3. Do not share passwords, recovery codes, or one-time verification codes.
4. Report suspicious messages to the security team according to organisational procedures.
5. If you have submitted credentials, use a trusted device to change the password immediately, revoke sessions, enable or reset MFA, and notify the service provider or organisational support team.

## K0-004 | Passwords and Multi-Factor Authentication
Do not reuse passwords across services. A password leaked from one service may be tried against other services; this is commonly known as credential stuffing. A password manager can help generate and store a unique password for each service.

Multi-factor authentication (MFA) requires evidence from different categories to verify identity, such as:
- Knowledge factor: a password or PIN.
- Possession factor: a security key or authenticator device.
- Inherence factor: certain biometric characteristics.

Using multiple passwords does not constitute multi-factor authentication because they belong to the same category. Phishing-resistant security keys or passkeys are generally stronger than relying only on SMS verification codes. MFA does not replace device updates, session protection, or least privilege.

## K0-005 | Updates, Backups, and Recovery
Software updates often fix vulnerabilities, stability issues, or compatibility problems. Delaying updates for long periods leaves known weaknesses in place. Before updating, assess business compatibility and prepare a rollback plan for critical systems.

Backups should:
- Be appropriately isolated from production systems so the same attack cannot easily destroy both production data and backups.
- Have backup frequencies and retention periods based on data importance.
- Be tested through regular recovery exercises, rather than checking only whether a “backup job succeeded.”
- Have their access permissions and encryption keys protected.

Two concepts are commonly used to describe recovery objectives: **RPO (Recovery Point Objective)** is the acceptable time range of data loss; **RTO (Recovery Time Objective)** is the target time needed to restore business operations. Both should be determined by business impact and risk.

## K0-006 | Authorisation, Law, and Professional Ethics
Security testing must take place within a clearly authorised scope. Authorisation should specify target assets, permitted testing methods, time windows, data-handling rules, contacts, stop conditions, and reporting procedures. Merely being able to access a system does not mean you are authorised to test it.

When discovering a vulnerability, avoid expanding access, downloading unnecessary data, or publicly disclosing sensitive details. Keep the minimum evidence needed to demonstrate the issue and follow the system owner's responsible disclosure process. Laws differ across countries and regions; real-world work must comply with applicable law, contracts, and organisational policies.

## K0-007 | Principle of Least Privilege
The principle of least privilege requires users, programs, and services to receive only the minimum permissions needed to perform their tasks, with access revoked when it is no longer required. Use a standard account for everyday work whenever possible and a controlled administrator identity for administrative tasks. Service accounts should avoid interactive logins; secrets should be stored securely and rotated periodically.

Excessive permissions increase the potential impact of a compromised account or exploited application. Regular permission reviews, removal of access for departing staff, separate administrative accounts, and logging of high-risk actions help reduce risk.

## References
- NIST Cybersecurity Framework: https://www.nist.gov/cyberframework
- CISA Secure Our World: https://www.cisa.gov/secure-our-world
- Microsoft Learn — Cybersecurity Fundamentals: https://learn.microsoft.com/en-us/training/paths/describe-basic-concepts-of-cybersecurity/
- NIST SP 800 Series: https://csrc.nist.gov/publications/sp800

---

<a id="l1--computer-and-operating-system-fundamentals"></a>

# L1 — Computer and Operating System Fundamentals

# L1 | Computer and Operating System Fundamentals: Core Knowledge

## K1-001 | Basic Computer Components
The CPU executes instructions; memory holds programs and data in use; a hard drive or SSD provides persistent storage; the network interface handles network communication; and the operating system manages hardware resources and provides services to applications. Security issues can occur at every layer: outdated hardware firmware, incorrectly configured system permissions, vulnerable applications, or unencrypted stored data can all affect overall security.

Understanding these components helps with troubleshooting. For example, an unresponsive application may be related to a process, memory, disk space, or the network. The symptoms alone are not enough to conclude that an attack is taking place.

## K1-002 | Operating Systems, Processes, and Services
An operating system manages processes, memory, files, devices, and user permissions. A **process** is an instance of a running program. A **service** is generally a background program or process that provides a function and may run at startup or on demand. The more functions a service exposes, the larger the potential attack surface may be, but service count alone does not determine risk.

Security practices include removing unnecessary software and services, applying updates promptly, restricting service permissions, recording service changes, and monitoring for unusual processes. Before terminating a process or disabling a service, confirm its purpose to avoid disrupting the system or business.

## K1-003 | File Systems and Permissions
A file system organises files and directories and stores metadata. The operating system uses permissions to determine which resources a subject may read, write, execute, or manage. Common Linux permissions are read (r), write (w), and execute (x), applied separately to the owner, group, and other users.

Overly broad permissions can expose sensitive information or allow it to be altered. Shared directories, scripts, backups, and configuration files should all follow the principle of least privilege. Do not solve a “permissions problem” by making a file or directory readable, writable, and executable by everyone. First determine which users and operations are actually required.

## K1-004 | Windows Security Fundamentals
Windows provides user accounts, groups, access controls, system updates, firewalls, event logs, and security features. Administrator privileges allow high-impact actions, so everyday activities should not routinely run with administrator rights. Logs in Event Viewer can help investigate login, service, system, and application events, but a single log entry usually cannot establish a complete attack sequence on its own.

Recommended practices: enable automatic updates or a managed update process; enable the firewall; restrict administrator accounts; use device encryption where applicable; review startup items and services; retain logs according to organisational policy; and avoid installing programs from untrusted sources.

Official documentation: https://learn.microsoft.com/windows/security/

## K1-005 | Linux Security Fundamentals
Linux uses users, groups, and permissions to control resource access, and system logs to record events. `sudo` allows authorised users to run specified administrative commands; it should be used only when needed, and its configuration should be reviewed. Install software primarily from trusted distribution repositories or official vendor channels.

Common concepts:
- `/etc` typically contains system configuration.
- `/var/log` is commonly used for logs, although locations vary by distribution and service.
- `ps` displays processes.
- `ip` displays and manages network-interface information.
- `systemctl` manages services on systems that use systemd.
- `journalctl` can display systemd logs.

Command output depends on permissions, system version, and configuration. Understand the side effects of administrative commands and consult the manual before running them. Do not run unknown scripts copied from the internet as root.

Official documentation: https://help.ubuntu.com/  
Linux manual pages: https://man7.org/linux/man-pages/

## K1-006 | Command Line, Shells, and Pipes
The command line lets users enter instructions as text. A command usually consists of a program name, arguments, and options. A pipe passes the output of one command to another; redirection sends input or output to a file.

Command-line skills help users inspect logs, filter data, and automate repetitive tasks, but incorrect arguments can delete data, overwrite files, or change system configuration. Before running a command, check the current directory, target path, and what the command does. Back up important data and test on a copy first.

## K1-007 | Virtual Machines and Isolated Lab Environments
A virtual machine simulates a separate computer on a host system and is useful for practising operating systems and security tools. A snapshot saves the virtual machine's state at a point in time and makes rollback easier, but it is not a substitute for an independent backup and may not capture the state of external systems or remote services.

For security labs, use an isolated network, fictional data, and dedicated test accounts. Do not expose vulnerable target machines directly to the public internet. Never reuse real passwords, company credentials, or customer information in a lab. At the end of an exercise, shut down services, restore snapshots, and remove temporary secrets.

## K1-008 | Hashes and File Integrity
A cryptographic hash function maps input of any length to a fixed-length digest. The same input produces the same digest with the same algorithm; when the input changes, the digest will usually change as well. Hashes can be used to compare whether a file has changed, identify known samples, and record evidence.

Hashing is not encryption: a hash is generally not directly reversible, while encryption is designed to allow decryption with a key. An ordinary hash does not automatically prove that a source is trustworthy; an attacker could replace both the file and its digest. To verify provenance, obtain the digest through a trusted channel or use a digital signature.

## References
- Microsoft Learn: https://learn.microsoft.com/training/
- Ubuntu Official Documentation: https://help.ubuntu.com/
- Linux man-pages: https://man7.org/linux/man-pages/
- OverTheWire Bandit (authorised practice environment): https://overthewire.org/wargames/bandit/

---

<a id="l2--networking-principles-and-basic-tools"></a>

# L2 — Networking Principles and Basic Tools

# L2 | Networking Principles and Basic Tools: Core Knowledge

## K2-001 | Network Communication Models
Network communication involves layers such as the link, network, transport, and application layers. Layered models help engineers narrow down problems, but the OSI model and the actual TCP/IP protocol stack do not correspond to a one-to-one physical structure. Troubleshooting should consider addressing, routing, protocols, application responses, and security policies rather than drawing conclusions from a single tool.

## K2-002 | IP Addresses, Subnets, and Routing
An IP address identifies an interface on an IP network. A subnet prefix indicates the number of bits used for the network portion of the address; routing determines where a packet is forwarded next. The default gateway is generally used to forward traffic outside the local subnet.

Address conflicts, incorrect subnet masks, wrong gateways, or routing policies can cause communication failures. Private IPv4 addresses are commonly used on internal networks and are not globally routable as unique addresses on the public internet. IPv6 uses different addressing and neighbour-discovery mechanisms. When troubleshooting, consider whether both IPv4 and IPv6 are enabled.

## K2-003 | TCP and UDP
TCP provides a connection-oriented, reliable, ordered byte stream, with mechanisms such as connection establishment, acknowledgements, retransmission, and flow control. UDP provides a lightweight datagram transport and does not guarantee delivery, ordering, or retransmission. Applications can implement their own reliability mechanisms on top of UDP.

Neither “TCP is more secure” nor “UDP is inherently insecure” is an accurate conclusion. Security depends on the application protocol, authentication, encryption, configuration, and deployment. TLS can provide encryption and authentication for many TCP-based applications; other protocols have their own security mechanisms.

## K2-004 | Ports and Services
Port numbers help the transport layer deliver data to the appropriate application or service. Common examples include HTTP on port 80, HTTPS on port 443, and DNS usually on port 53, although deployments may use non-default ports or different transport methods. An open port indicates a form of network reachability or a listening state; it does not directly prove that a vulnerability exists.

Security management should maintain a service inventory, close unnecessary listening services, restrict network access to administrative interfaces, and combine authentication, patching, logging, and network segmentation. Changing a port number is not a substitute for proper security controls.

## K2-005 | The Role of DNS
DNS maps domain names to records, such as A/AAAA address records, MX mail-exchange records, and CNAME aliases. Resolution commonly involves recursive resolvers and authoritative name servers. DNS caching improves efficiency, but caches and TTL values affect how quickly changes take effect.

DNS issues may appear as failed name resolution, resolution to an incorrect address, or inconsistent results across networks. Troubleshooting should compare local caches, recursive resolvers, and authoritative records, while recording query times and responses. DNSSEC can help verify the origin and integrity of DNS data, but it does not make query contents confidential or eliminate every domain-related risk.

## K2-006 | HTTP, HTTPS, and TLS
HTTP is an application-layer protocol that defines requests and responses. HTTPS is HTTP communication protected by TLS. TLS can provide transport encryption and integrity protection and, when certificates are validated correctly, help a client verify the server's identity.

TLS does not prove that a website's content is trustworthy, prevent endpoint compromise or phishing, or fix incorrect server authorisation settings. Certificate errors should not be casually ignored. Applications still need correctly implemented authentication, authorisation, input handling, session management, and logging.

References: HTTP Semantics specification https://www.rfc-editor.org/rfc/rfc9110  
TLS 1.3 specification https://www.rfc-editor.org/rfc/rfc8446

## K2-007 | Firewalls, Proxies, and VPNs
A firewall allows or blocks network traffic according to rules. Rules may be based on addresses, ports, protocols, connection state, or application context. Overly permissive rules increase exposure, while overly restrictive rules can interrupt legitimate business. Changes should therefore be recorded and tested.

A proxy forwards requests on behalf of a client or server and may be used for access control, caching, logging, or content inspection. A VPN establishes a protected tunnel between networks or between a device and a network. A VPN does not automatically make an endpoint secure, nor does it mean a user should be able to access every internal resource. MFA, least privilege, endpoint protection, and logging remain necessary.

## K2-008 | Basic Network Diagnostic Tools
- `ping`: tests ICMP reachability; a blocked response does not necessarily mean the host is unavailable.
- `traceroute` / `tracert`: observes responses along a network path; a non-responsive intermediate node does not necessarily indicate a fault.
- `ipconfig`, `ip addr`: display local network configuration.
- `nslookup` or `dig`: check DNS resolution.
- `curl`: sends HTTP requests and displays responses.
- Wireshark: examines captured network packets in an authorised environment.

Tool output is part of the evidence, not the complete conclusion. Record the time, environment, command arguments, results, and possible limitations. Do not scan or test third-party systems without authorisation.

## K2-009 | Uses of Python in Security Work
Python can be used to parse logs, organise CSV/JSON data, analyse events, call APIs, and automate repetitive tasks. Fundamental skills include variables, conditionals, loops, functions, exception handling, file I/O, and data structures.

Security scripts should validate input, handle exceptions, avoid exposing sensitive data in logs, and store secrets in secure configuration or a secrets-management system. Automation can amplify mistakes, so begin with sample data and a test environment, then review the output before using it in production.

## References
- Cisco Networking Academy: https://www.netacad.com/
- Wireshark Documentation: https://www.wireshark.org/docs/
- Python Tutorial: https://docs.python.org/3/tutorial/
- RFC Editor: https://www.rfc-editor.org/

---
<a id="l3--core-cybersecurity-principles"></a>

# L3 — Core Cybersecurity Principles

# L3 | Core Cybersecurity Principles: Core Knowledge

## K3-001 | Defence in Depth
Defence in depth uses multiple complementary security controls to reduce the impact of any single control failing. For example, account security may combine MFA, least privilege, login alerts, device protection, and recovery procedures. Layers of control should avoid common points of failure where possible; for example, using the same administrator account for all backups weakens isolation.

Defence in depth is not simply a matter of stacking products. Each control should have a clear objective, owner, monitoring method, and failure-handling process, and its continued effectiveness should be verified regularly.

## K3-002 | Authentication, Authorisation, and Auditing
Authentication confirms who a subject is; authorisation determines what the subject can do; auditing records what the subject has done. These functions are related but cannot replace one another. A successful login does not mean a user should be allowed to access all information.

Common controls include MFA, role-based access control (RBAC), attribute-based access control (ABAC), session timeouts, separation of privileged accounts, and periodic access reviews. Systems should deny access by default unless it has been explicitly allowed, and record traceable audit events for sensitive operations.

## K3-003 | Password Storage and Cryptography
A server should not store user passwords in plaintext. Password verification usually relies on a purpose-built password-hashing scheme, with a unique random salt for each user and an appropriate computational cost. Ordinary fast hash algorithms are not suitable as password-storage schemes.

Encryption, hashing, and digital signatures serve different purposes:
- Encryption protects the confidentiality of content under control of a key.
- Hashing generates a digest and is commonly used for integrity checks and indexing.
- Digital signatures help verify the key used to sign a message and the message's integrity, but management of signing keys and their binding to identities remain important.

Restrict access to keys, avoid hard-coding them, back them up appropriately, and define rotation and revocation procedures. Use reviewed standard libraries and protocols; do not design your own cryptographic algorithms.

## K3-004 | Vulnerability Management Lifecycle
Vulnerability management commonly includes asset identification, scanning or assessment, validation, prioritisation, remediation, retesting, and reporting. Scanner results may include false positives and may miss issues, so high-impact findings should be validated manually and assessed in the context of the relevant assets.

Priorities should not be based on severity scores alone. Consider whether an asset is exposed to the public internet, whether exploitation conditions exist, business importance, existing mitigating controls, and remediation cost. After remediation, retest and record evidence. If immediate remediation is not possible, record the risk owner, compensating controls, and review deadline.

CVE identifies publicly disclosed vulnerabilities; CVSS describes technical vulnerability severity and is not the same as an organisation's own business risk.

## K3-005 | Security Logging and Monitoring
Logs are important evidence for investigating incidents. Common sources include identity systems, endpoints, network devices, cloud platforms, applications, and databases. Effective logging requires time synchronisation, appropriate fields, access controls, integrity protection, and a retention policy.

An alert is a signal triggered by a rule or model; it is not the same as a confirmed security incident. Analysts should check context, related events, asset importance, and normal business activity, and document any uncertainty in their conclusions. Logs should not retain passwords, access tokens, or excessive personal data unnecessarily.

## K3-006 | Incident Response
Incident response aims to reduce impact, restore trustworthy operations, and learn from the event. Common phases include preparation, identification and analysis, containment, eradication, recovery, and post-incident review. In a real incident, these phases may overlap, and the organisation's response plan and legal obligations should be followed.

Important principles:
- Protect people and business operations, and escalate to the responsible team when necessary.
- Preserve relevant logs and evidence; do not clear or reinstall a system before assessing the consequences.
- Consider business impact and evidence preservation when choosing containment measures.
- Before recovery, confirm that the root cause has been addressed and increase monitoring.
- Focus post-incident reviews on systemic improvements rather than merely assigning individual blame.

## K3-007 | Backups, Business Continuity, and Recovery
Backup strategies should be based on data importance and business recovery requirements. RPO describes the acceptable range of data loss; RTO describes the desired recovery time. The existence of backups does not guarantee successful recovery: recovery exercises must be conducted regularly, and the time taken and any gaps should be recorded.

Consider offline or isolated copies, access permissions, encryption, retention policies, and monitoring of the backup system itself. Recovery procedures must also account for identity systems, keys, network dependencies, and the order in which business services need to be restored—not just the restoration of files.

## K3-008 | NIST Cybersecurity Framework 2.0
The NIST CSF 2.0 is a high-level framework for managing organisational cybersecurity risk. Its core functions are Govern, Identify, Protect, Detect, Respond, and Recover. It helps organisations discuss objectives, current state, gaps, and priorities, but it is not a fixed checklist that applies identically to every organisation and does not replace specific technical standards or legal requirements.

Official source: https://www.nist.gov/cyberframework

## References
- NIST CSF: https://www.nist.gov/cyberframework
- NIST SP 800 Series: https://csrc.nist.gov/publications/sp800
- CIS Critical Security Controls: https://www.cisecurity.org/controls
- MITRE ATT&CK: https://attack.mitre.org/

---

<a id="l4--common-security-issues-and-defensive-practices"></a>

# L4 — Common Security Issues and Defensive Practices

# L4 | Common Security Issues and Defensive Practices: Core Knowledge

## K4-001 | Basic Structure of a Web Application
A web application usually includes components such as a browser, web server, application logic, and database. The browser sends HTTP requests; the server processes them according to routing, identity, and business logic, then returns responses. Security issues can arise in input handling, authentication, authorisation, sessions, business logic, dependencies, or deployment configuration.

Hiding a button on the client side is not an authorisation control, because a request can be constructed directly. The server must verify identity and permissions for every sensitive operation.

## K4-002 | Access Control Flaws
Access control determines which resources an authenticated user may access and which operations they may perform. Typical flaws include ordinary users reaching administrator functions, users reading another person's objects, bypassing business workflows, or changing a resource identifier to gain unauthorised access.

Defences:
- Perform authorisation checks on the server for every request.
- Use a default-deny policy and least privilege.
- Do not treat random or hard-to-guess object IDs as an authorisation mechanism.
- Create test cases for different roles and verify both allowed and denied paths.
- Log sensitive access and monitor unusual behaviour.

## K4-003 | Root Causes of Injection Vulnerabilities
Injection occurs when a program incorrectly interprets untrusted input as instructions or query syntax. SQL injection is one example. Key defences include parameterised queries, avoiding the construction of queries by concatenating untrusted input, least-privilege database permissions, and appropriate error handling.

Input filtering can be a supplementary measure, but it should generally not replace correctly parameterised interfaces. Error messages should not expose database structure, secrets, or internal stack traces to untrusted users. Testing should be performed in a dedicated lab or on an application for which testing is authorised.

## K4-004 | Cross-Site Scripting (XSS)
XSS is a class of vulnerability in which attacker-controlled content executes as a script in a victim's browser. The risk depends on how data enters a page, its context, and browser security controls. Common defences include context-aware output encoding, avoiding unsafe DOM operations, using secure frameworks with automatic escaping, and applying a reasonable Content Security Policy (CSP) as a defence-in-depth measure.

Simply removing certain characters is often insufficient to prevent XSS because HTML, attribute, URL, and script contexts require different handling. Apply appropriate encoding for the context in which the data is used and validate it in an authorised test environment.

## K4-005 | Cross-Site Request Forgery (CSRF)
CSRF takes advantage of the fact that a browser may automatically attach session credentials, causing an authenticated user to submit an unintended action. Defences may include CSRF tokens, appropriate SameSite cookie attributes, validation of Origin/Referer where suitable, reauthentication for high-risk operations, and avoiding state-changing actions through GET requests.

SameSite is not a complete substitute in every scenario. Design defences based on the authentication method, cross-site business requirements, and browser behaviour.

## K4-006 | Authentication and Session Security
Authentication systems must verify identity securely and manage login state. Common risks include weak password policies, leaked credentials, session fixation, exposed tokens, sessions that remain valid after logout, and weak account-recovery processes.

Defences include MFA, rate limiting and risk detection, cryptographically secure random session identifiers, appropriate Secure/HttpOnly/SameSite cookie attributes, session renewal when privileges change, server-side token invalidation on logout, and protected password-reset procedures. Do not put session tokens in URLs or logs.

## K4-007 | Input Validation and Output Encoding
Input validation checks whether data conforms to expected formats, ranges, and business rules. Output encoding converts special characters into a safe representation for the context in which the data will be used. They serve different purposes: input validation should not be treated as a universal defence for every output context.

Use explicit permitted formats and ranges for fields such as dates, quantities, and enumerated values. Avoid unnecessarily rejecting legitimate free text, and encode it correctly when outputting it. File uploads should also be restricted by type, size, storage location, and processing permissions; do not trust only the file extension supplied by the client.

## K4-008 | Uses and Limitations of the OWASP Top 10
The OWASP Top 10 is an awareness and education resource covering important common web-application risks. It helps teams recognise risk categories such as access-control failures, misconfiguration, supply-chain issues, cryptography, and injection. It is not a complete testing checklist and cannot prove that an application is “secure.” More detailed verification can be performed using the OWASP ASVS and Web Security Testing Guide.

Official resources:
- OWASP Top 10: https://owasp.org/www-project-top-ten/
- OWASP ASVS: https://owasp.org/www-project-application-security-verification-standard/
- OWASP WSTG: https://owasp.org/www-project-web-security-testing-guide/
- PortSwigger Web Security Academy: https://portswigger.net/web-security

## K4-009 | Basic Structure of a Security Test Report
A reproducible report should include the testing authorisation and scope, system and version, methods, findings, evidence, impact, basis for severity, remediation recommendations, retest results, and limitations. Conclusions should distinguish observed facts from inferences. Minimise evidence and remove passwords, tokens, personal information, and other sensitive data that is not necessary.

## References
- OWASP Top 10: https://owasp.org/www-project-top-ten/
- OWASP ASVS: https://owasp.org/www-project-application-security-verification-standard/
- OWASP WSTG: https://owasp.org/www-project-web-security-testing-guide/
- PortSwigger Web Security Academy: https://portswigger.net/web-security

---
<a id="l5--core-knowledge-for-cybersecurity-specialisations"></a>

# L5 — Core Knowledge for Cybersecurity Specialisations

# L5 | Core Knowledge for Cybersecurity Specialisations

This level covers core concepts across several specialisations. For practical study, it is recommended that learners choose one primary area to explore in depth while maintaining a basic understanding of the others.

## K5-001 | Blue Team, SOC, and Security Operations
The blue team protects systems, detects anomalies, investigates incidents, and improves defences. A SOC (Security Operations Centre) commonly handles centralised monitoring, alert triage, investigation escalation, and operational reporting. Security operations depend not only on tools, but also on asset context, clear procedures, and continuous review.

A common workflow:
1. Receive an alert and confirm its source and the meaning of the rule that triggered it.
2. Determine which accounts, devices, times, networks, and business activities are involved.
3. Correlate other logs and rule out common false positives.
4. Decide whether to escalate, contain, or close the alert based on impact and evidence.
5. Record evidence, conclusions, actions, and follow-up improvements.

A high alert score does not necessarily mean a real attack is occurring, and a low score does not necessarily mean there is no risk. Analysis should consider asset importance, detection-rule limitations, and possible attacker evasion.

Resources:
- MITRE ATT&CK: https://attack.mitre.org/
- CyberDefenders: https://cyberdefenders.org/
- Splunk free courses: https://www.splunk.com/en_us/training/free-courses/overview.html

## K5-002 | Penetration Testing and Application Security
Penetration testing simulates specific attack scenarios within a clearly authorised scope to validate security weaknesses. Professional testing involves more than finding issues: it also includes controlling impact, preserving evidence, explaining risk, recommending remediation, and retesting.

The test plan should specify target assets, permitted methods, time windows, data handling, contacts, prohibited activities, and stop conditions. After finding an issue, do not access data beyond the authorised scope or disrupt business operations merely to demonstrate impact. Results must describe the environment and scope; failure to find an issue in one test does not mean the system is absolutely secure.

Resources:
- PortSwigger Web Security Academy: https://portswigger.net/web-security
- OWASP WSTG: https://owasp.org/www-project-web-security-testing-guide/
- OWASP ASVS: https://owasp.org/www-project-application-security-verification-standard/

## K5-003 | Digital Forensics and Incident Response (DFIR)
Digital forensics focuses on collecting, preserving, analysing, and presenting digital evidence in a reproducible way. Incident response focuses on reducing the impact of security incidents and restoring trustworthy operations. The two overlap, but their primary emphases differ.

Key principles include recording evidence sources, timestamps, collectors, and handling steps; keeping original evidence read-only wherever possible; analysing copies; recording tool versions and hashes; accounting for time zones and system-clock differences; and distinguishing facts, inferences, and unknowns. A hash can help detect changes to content, but it cannot by itself prove the origin of evidence or that the collection process was trustworthy.

Resources:
- Autopsy: https://www.autopsy.com/
- Volatility Foundation: https://volatilityfoundation.org/
- NIST SP 800 Series: https://csrc.nist.gov/publications/sp800
- CyberDefenders: https://cyberdefenders.org/

## K5-004 | Cloud Security
Cloud security is based on a shared responsibility model: the cloud service provider secures parts of the underlying infrastructure, while customers remain responsible for identity, data, configuration, applications, access control, and other areas according to the service type. Responsibility boundaries vary across IaaS, PaaS, SaaS, and individual services. Do not assume that being “in the cloud” automatically makes something secure.

Common controls include MFA, least privilege, short-lived credentials, key management, network segmentation, logging and alerts, storage-access restrictions, configuration baselines, backups, and recovery testing. Cloud resources can be exposed through misconfiguration, so maintain an asset inventory, review changes, and continuously monitor configuration.

Resources:
- AWS Security: https://docs.aws.amazon.com/security/
- Microsoft Security: https://learn.microsoft.com/en-us/security/
- Google Cloud Security: https://cloud.google.com/security
- CIS Benchmarks: https://www.cisecurity.org/cis-benchmarks

## K5-005 | Application Security (AppSec)
Application security should be integrated throughout requirements, design, development, testing, deployment, and maintenance. Threat modelling identifies assets, trust boundaries, data flows, abuse scenarios, and potential control gaps. Secure code review, dependency checking, secret scanning, static analysis, and dynamic testing can find different categories of problems, but no single tool covers every risk.

Secure development practices include secure-by-default configuration, server-side authorisation, parameterised queries, dependency updates, secrets management, code review, build-provenance verification, and retesting after vulnerability fixes. Findings from scans should be validated by people, and real secrets should never be committed to repositories or written to logs.

Resources:
- OWASP: https://owasp.org/
- GitHub Code Security: https://docs.github.com/en/code-security
- Microsoft SDL: https://www.microsoft.com/en-us/securityengineering/sdl

## K5-006 | Governance, Risk, and Compliance (GRC)
GRC connects governance responsibilities, risk decisions, and compliance requirements. An organisation needs to identify assets and business objectives, assess risk, select controls, assign owners, and retain reviewable evidence. Passing a compliance assessment does not automatically eliminate risk; standards, laws, contracts, and business risks should be understood separately.

A risk register commonly records the risk description, affected assets, likelihood, impact, existing controls, treatment plan, owner, deadline, and residual risk. Common treatment options include mitigation, avoidance, transfer, or acceptance of the risk by an authorised party. Risk acceptance should be made by someone authorised to bear the consequences and reviewed periodically.

Resources:
- NIST CSF: https://www.nist.gov/cyberframework
- CIS Controls: https://www.cisecurity.org/controls
- ISO/IEC 27001: https://www.iso.org/isoiec-27001-information-security.html

## K5-007 | Relationships Between Cloud, Blue Team, Red Team, and GRC
These specialisations do not replace one another. Cloud security focuses on cloud resources and identity configuration; the blue team handles detection and response; penetration testing validates weaknesses within a specific authorised scope; and GRC organises risk, accountability, controls, and evidence. Mature security programmes require collaboration across these areas: testing findings become remediation tasks, the blue team validates detection capabilities, cloud teams implement configuration changes, and GRC tracks risk closure and supporting evidence.

## References
- MITRE ATT&CK: https://attack.mitre.org/
- OWASP: https://owasp.org/
- NIST CSF: https://www.nist.gov/cyberframework
- CIS Controls: https://www.cisecurity.org/controls

---

<a id="l6--advanced-security-engineering-and-research"></a>

# L6 — Advanced Security Engineering and Research

# L6 | Advanced Security Engineering and Research: Core Knowledge

## K6-001 | Threat Modelling
Threat modelling is the systematic process of identifying assets, attack surfaces, trust boundaries, abuse scenarios, and security controls during system design or change. It helps teams discover design risks before they reach production, rather than relying only on post-deployment scanning.

Common steps:
1. Describe system components, data flows, and external dependencies.
2. Identify trust boundaries, sensitive assets, and high-impact operations.
3. List abuse scenarios and potential failure modes.
4. Assess impact, likelihood, and existing controls.
5. Assign mitigations, owners, and verification criteria.
6. Update the model when the architecture or business changes significantly.

A threat model is not a one-time document. It should be reviewed as the system, dependencies, and threat environment change.

Resource: https://owasp.org/www-community/Threat_Modeling

## K6-002 | Detection Engineering and Threat Hunting
Detection engineering turns security hypotheses into verifiable log queries, rules, and alerts. Threat hunting usually starts with a hypothesis or anomaly and proactively examines telemetry to look for behaviour not covered by existing alerts.

A high-quality detection should describe the behaviour to identify, required data sources, query logic, expected signals, sources of false positives, test data, coverage limitations, and response actions. After deployment, continuously evaluate false positives, false negatives, data quality, and business changes. A detection rule without log data may provide only theoretical coverage.

MITRE ATT&CK describes adversary tactics and techniques and can help organisations map observed behaviour to detection capabilities. However, the number of ATT&CK techniques covered should not be treated directly as a measure of security maturity.

Resources:
- MITRE ATT&CK: https://attack.mitre.org/
- Sigma: https://sigmahq.io/

## K6-003 | Security Architecture and Zero Trust
Security architecture organises identity, devices, networks, applications, data, monitoring, and governance controls into a coherent system. Zero trust is not a single product, but a set of design principles: do not automatically trust a subject because of its network location; evaluate access requests according to identity, device state, resource sensitivity, and policy; and continuously monitor access while limiting permissions.

Zero trust does not mean that every request must use the same authentication method, nor does it mean network segmentation is no longer needed. Its goals are to reduce implicit trust, narrow access, and improve the visibility of access decisions.

## K6-004 | Advanced Incident Response and Root-Cause Analysis
Advanced incident response correlates evidence from multiple sources into a timeline and assesses the scope of impact, initial access path, privilege changes, lateral activity, data impact, and recovery status. Time-related data may be affected by time zones, clock drift, logging delays, and missing collection. These limitations must be recorded during analysis.

Root-cause analysis should not stop at statements such as “a file was executed” or “an account was compromised.” It should also identify systemic contributing factors, such as weak identity controls, exposed assets, patch-management processes, monitoring gaps, or recovery-design issues, and propose improvements that can be verified.

## K6-005 | Safety Principles for Malware Analysis
Malware analysis aims to understand the behaviour, impact, and detection indicators of a file or program. Unknown samples can infect devices, expose data, or spread across networks. They should therefore be handled in a dedicated isolated lab with a controlled network and fictional data, in accordance with the organisation's sample-handling policy.

An analysis report should record the sample source, hash, tools and versions, environment, observed behaviour, evidence, and limitations. A label from a single detection engine does not independently prove that a file is malicious; similarly, a file not being detected does not prove it is safe. Never run unknown samples on a computer used for everyday work.

Resources:
- REMnux: https://remnux.org/
- Volatility Foundation: https://volatilityfoundation.org/
- NIST: https://csrc.nist.gov/publications/sp800

## K6-006 | Reproducibility in Security Research
Reproducible research clearly describes the research question, environment, versions, data sources, methods, observations, limitations, and ethical boundaries. Other researchers should be able to understand how the conclusions were reached, rather than seeing only screenshots or tool output.

Researchers should distinguish between:
- **Fact:** An observation directly supported by records or evidence.
- **Inference:** An explanation supported by multiple facts but still subject to uncertainty.
- **Hypothesis:** A possibility that needs further verification.
- **Unknown:** A question that current evidence cannot answer.

Vulnerability research should follow authorisation and responsible disclosure. Avoid publishing sensitive details that would make exploitation easy for others or exposing real user data.

## K6-007 | Security Metrics and Continuous Improvement
Security metrics should connect to business risk and control objectives, rather than merely counting tools or total alerts. Useful measures can include patch timeliness for critical assets, MFA coverage, backup-recovery test success rate, overdue high-risk items, alert-handling time, detection-rule false-positive rate, and incident recurrence.

Metrics need clearly defined denominators, data sources, measurement periods, and interpretation limits. Simply aiming for fewer alerts may cause missed detections; aiming to close incidents faster may reduce investigation quality. Evaluate quality measures, business impact, and lessons learned together.

## References
- NIST Cybersecurity Framework: https://www.nist.gov/cyberframework
- NIST SP 800 Series: https://csrc.nist.gov/publications/sp800
- MITRE ATT&CK: https://attack.mitre.org/
- OWASP Threat Modeling: https://owasp.org/www-community/Threat_Modeling
- REMnux: https://remnux.org/

---
