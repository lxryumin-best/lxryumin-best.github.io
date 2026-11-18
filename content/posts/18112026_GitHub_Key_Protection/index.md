---
title: "GitHub Key Protection: Least Privilege for AI Agents"
date: 2026-11-18T12:00:00+03:00
draft: false
description: "A practical model for protecting GitHub keys: one-repo deploy keys, least privilege for an AI agent, secret scanning, and a plan for the day a key leaks."
tags: ["GitHub Security", "Secrets Management", "SSH Keys", "Least Privilege", "DevSecOps"]
---

**The Context (Business Challenge / Problem):**
Recently I connected an AI assistant to the GitHub repository behind this portfolio. It can now draft an article, place it into the Hugo structure, run the build, and publish. The first design question was not "what can it write?" It was "what can it reach?"

A GitHub key is not a password. It is delegated authority. A personal token with broad repository scope can read every private repository you can see, rewrite branches, and push code that runs in your CI. A deploy key is narrower, but if it is stored in the wrong place, it is just as dangerous. This portfolio is public, so the immediate blast radius is small. The pattern is what matters: the same shortcut applied to a client repository can turn a convenient automation into a supply-chain incident.

Every automation adds a credential. Every credential adds a path that does not require a human. The goal is not to trust the assistant more. The goal is to make the key small enough that trust is not the only control.

**The Architecture & Work (Solution):**
I use six controls. None of them is exotic. The value is in applying all of them to one small workflow.

**1. Choose the narrowest credential type.**
A classic personal access token is account-wide. A fine-grained token can be limited to selected repositories and permissions. A deploy key is limited to one repository. A GitHub App is limited to an installation. OIDC removes the long-lived cloud secret entirely. For an assistant that only publishes articles, a deploy key with write access to one repository is enough. There is no reason to hand it an account-wide token.

**2. Separate reading from writing.**
Reading a public repository is cheap and low-risk. Writing is where damage happens. In this setup, the assistant reads the repository through the public API and writes through exactly one channel: a repository-scoped SSH key. There is no second write path, no token in an environment file, no "just in case" credential. One channel is easier to watch than five.

**3. Keep the private key outside the synced workspace.**
The working folder of this project is mirrored to cloud storage. That is convenient for drafts and terrible for secrets. The private key lives in a dedicated directory outside the sync, with permissions `600`. The SSH config applies it only to `github.com`. The repository's `.git/config` contains no token. If the key is ever copied into a note, a chat, or a commit, it is already compromised — treat it that way.

**4. Make the key boring.**
One repository, one job, one place. Name the key after the workflow, not after the person. Write down why it exists and when it was last reviewed. A key that can be revoked in one click is a key you can afford to lose.

**5. Add a gate before publication.**
Access control decides who can push. It does not catch a password pasted into an article. Before the Hugo build, a validator scans the content for literal credentials and IPv4 addresses and fails the pipeline if it finds one. The rule is intentionally blunt: if the text looks like a secret, the build stops. The validator is not a replacement for secret scanning. It is the last cheap check before publication.

**6. Plan the leak before it happens.**
The order matters. Revoke the key first, then investigate. If a secret reached git history, revoking stops the bleeding; cleaning history with `git filter-repo` prevents the next reader from finding it. Force-push the cleaned branch and check the security log. Then write down what happened. A key rotated after an incident is a lesson. A key rotated before is a process.

On GitHub's side, a few controls are worth enabling even for a solo repository: secret scanning and push protection, minimal `permissions` in Actions workflows, no secrets in logs, third-party actions pinned to a commit SHA. None of them is sufficient alone. Together they reduce the number of ways a single mistake becomes a public incident.

**The Takeaway (Business Value):**
The assistant did not need my account. It needed one repository, one write channel, and a clear boundary. The result is a publishing workflow that can be audited in a few minutes: one deploy key, one validation gate, one revoke button.

That is the standard I want for client infrastructure as well. Do not start with "how much can this automation do?" Start with "what is the smallest key that still does the job?" A key that cannot reach the client database, the cloud account, or the second repository is a key you can give to an agent without losing sleep.

Trust is not a security control. Scope is.
