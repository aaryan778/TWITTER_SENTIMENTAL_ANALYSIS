# WELCOME & COMMUNICATIONS — Channel Docs

---

## #announcements

So this channel is basically the front page of the server. If something important is happening with the project — a new release, a major architectural decision, a sprint kicking off, someone joining the team — it goes here first. Think of it like the one channel everyone should have notifications turned on for.

Only Aaryan posts here. That's intentional. If it's in announcements, it matters. We're not using this for casual updates or "hey I pushed a small fix" kind of stuff. This is for things that affect the whole team or change how we're working.

**What belongs here:**
- New sprint starting or ending
- Major milestone reached (e.g., RCA engine v1 shipped)
- New team member joining
- Big architectural decisions that affect everyone
- Server or tooling changes (new bot added, channel restructured, etc.)
- Any outage or production-level issue that the whole team needs to know about immediately

**What doesn't belong here:**
- Day-to-day progress updates (that's what `#daily-status-updates` is for)
- Questions or discussion (take it to `#general-discussion`)
- PR notifications (those go to `#pull-request-reviews` automatically)

**Format to follow when posting:**
```
📌 [TYPE] — Short Title

What happened / what's changing:
...

What you need to do (if anything):
...

— Aaryan
```

If you see something in here, read it fully. Don't just skim it.

---

## #general-discussion

This is the main room. Everything that doesn't have a dedicated channel, anything that's loosely related to the project, random technical questions, things you're stuck on, ideas you want to float — all of that lives here.

It's intentionally low-structure. The only rule is keep it related to the project or the tech stack in some way. This isn't a memes channel (we don't have one, and that's on purpose — keep things focused).

**What belongs here:**
- Quick questions that don't fit anywhere else
- Sharing something interesting you read that's relevant to what we're building
- Asking for a second opinion on something
- Casual technical discussion that isn't deep enough to warrant its own thread
- "Hey has anyone dealt with X before?" kind of stuff

**What doesn't belong here:**
- Anything that belongs in a specific channel — if there's a more appropriate place, use it
- Long design discussions (start a thread or take it to the relevant channel)

**Tips:**
- If your message starts a real conversation, hit the thread button and continue it there. Keeps the main channel from getting buried.
- If you're sharing a link, add a one-liner about why it's relevant. Don't just drop a URL.

---

## #team-introductions

Every person who joins the server posts here once. That's it. Just a short intro so everyone knows who's who, what you're working on, and what your background is. It doesn't have to be formal — write it like you'd introduce yourself at the start of a meeting.

**Template (use this loosely, don't copy-paste robotically):**
```
Name: 
Role on ASTRA: 
Background / what I work with: 
What I'm focused on right now: 
One thing I want to get out of this project: 
```

Nobody's grading this. The point is that when Bhargav asks Asif a question two months from now, they already have context on each other. Small teams work better when people actually know each other.

**Rules:**
- One post per person. If you want to update your intro, edit the original — don't post a new one.
- No replies in this channel. If you want to respond to someone's intro, DM them or say hi in `#general-discussion`.

---

## #resources-and-references

Think of this as the team's shared bookmarks folder. Anything useful — papers, tools, architecture references, eraser.io diagrams, blog posts, documentation links, YouTube videos that explain a concept well — goes here.

The goal is that if someone new joins six months from now, they can scroll through this channel and get up to speed on what we've been reading and thinking about.

**What belongs here:**
- Research papers related to RCA, log analysis, LLMs, observability
- Architecture diagrams (eraser.io exports, draw.io files, screenshots)
- Documentation links for tools we're using (Ollama, CloudWatch, Grafana, etc.)
- Good blog posts or articles on topics relevant to ASTRA
- Any reference implementations or open-source projects we're drawing inspiration from
- Meeting notes or decision logs that the whole team should be able to find

**How to post:**
Don't just drop a link. Add context:
```
📎 [TOPIC] — Title or brief description
Link: ...
Why it's relevant: one or two sentences
```

**Tags to use at the start of your message so things are searchable:**
- `[PAPER]` — research paper
- `[TOOL]` — software or service
- `[DIAGRAM]` — architecture or flow diagram
- `[ARTICLE]` — blog post or write-up
- `[DOCS]` — official documentation
- `[VIDEO]` — video explanation or talk
- `[DECISION]` — a record of a team decision

---

## #daily-status-updates

Every morning at 9AM CDT, the ASTRA bot drops an automated digest in this channel. It pulls from GitHub Projects and GitHub itself to give the whole team a snapshot of where things stand.

**What the bot posts:**

```
📋 ASTRA Daily Digest — Monday, April 7

OPEN TASKS
  In Progress  →  4 tasks
    - Build RCA Engine v1          (Bhargav, Asif)
    - API authentication setup     (Nithish)
    - Ollama server config         (Sai Purna)
    - EC2 simulation design        (Bhargav)

  Backlog      →  7 tasks
  In Review    →  1 task
  Done         →  2 tasks closed yesterday

PULL REQUESTS
  Awaiting Review  →  2 open PRs
    - PR #18: RCA prompt refactor  (opened by Asif)
    - PR #19: DB schema migration  (opened by Nithish)

INCIDENTS
  Active  →  0
  Opened yesterday  →  0

───────────────────────────────
Have a good one. — ASTRA Bot
```

**Beyond the bot:**

This channel is also for personal daily updates if you want to post them. It's not mandatory but it's encouraged. Just a quick note about what you're doing today. Nothing formal.

```
Working on the Ollama server config today. Hit a port conflict issue yesterday,
trying a different approach. Should have something testable by EOD.
— Sai Purna
```

**Rules:**
- Don't have unrelated conversations in here. If the digest sparks a discussion, take it to `#general-discussion` or the relevant channel.
- If you post a personal update, keep it short. Three sentences max.
