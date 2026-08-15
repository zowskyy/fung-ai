# Creator Storage Architecture

**Question**: How does project context get saved over chat histories, different project folders, and workflows? Where does all that save when there's no sign-up?

**Answer**: Everything is stored **locally in `~/.creator/`** — no cloud, no sign-up, completely offline-capable.

---

## Storage Overview

```
~/.creator/                          # User home (.creator hidden folder)
├── workspace/                       # All projects live here
│   ├── my-game/                     # One project folder
│   │   ├── project.json             # Project metadata (name, template, fields)
│   │   ├── files/                   # Actual code files
│   │   │   ├── main.py
│   │   │   ├── hero.png
│   │   │   └── ...
│   │   └── .git/                    # Full git history (saved versions)
│   │       ├── objects/             # Git objects
│   │       ├── refs/                # Git refs
│   │       └── logs/
│   │
│   ├── chat-bot/                    # Another project
│   │   ├── project.json
│   │   ├── files/
│   │   └── .git/
│   │
│   └── ... (unlimited projects)
│
├── conversations/                   # AI chat histories (v0.2.0+)
│   ├── abc12345.json                # One conversation thread
│   ├── def67890.json                # Another thread
│   └── ... (all chats saved forever)
│
├── auth.json                        # API keys (optional)
│   ├── openrouter_api_key
│   ├── groq_api_key
│   └── (user's own keys, if provided)
│
└── settings.json                    # App preferences
    ├── last_project
    ├── theme
    └── (user's window size, etc.)
```

---

## The Data Flow: From Creation to Long-Term Storage

### Step 1: User Creates a Project

**No sign-up needed** — everything happens locally.

```
1. User clicks "Create a new project"
2. Selects template (2D platformer, Python, Java, etc.)
3. Fills in fields ("hero name", "colors", etc.)
4. Creator generates files → stored in ~/.creator/workspace/{project-slug}/files/
5. Git repo initialized → ~/.creator/workspace/{project-slug}/.git/
6. Project metadata saved → ~/.creator/workspace/{project-slug}/project.json
```

**Files created**:
```json
// project.json
{
  "name": "My Game",
  "template": "2d-platformer",
  "created": "2026-08-14 12:00:00",
  "fields": {
    "hero_name": "Pixel",
    "hero_color": "blue",
    "bg_color": "green"
  }
}
```

### Step 2: User Chats with AI

**No API key needed** — cycles through free providers automatically.

```
1. User opens "Ask AI" tab
2. Types: "Make the hero jump higher"
3. Creator picks next available free provider (BlockRun, Groq, etc.)
4. Sends request → streams response
5. Conversation saved to ~/.creator/conversations/{conversation-id}.json
6. Project context attached (which files, current state)
```

**Conversation file**:
```json
// ~/.creator/conversations/abc12345.json
{
  "id": "abc12345",
  "created_at": 1723685400.5,
  "last_updated": 1723685450.2,
  "project_id": "my-game",  // Links to project
  "messages": [
    {
      "role": "user",
      "content": "Make the hero jump higher",
      "timestamp": 1723685400.5
    },
    {
      "role": "assistant",
      "content": "I'll increase the jump velocity... [code suggestion]",
      "timestamp": 1723685405.1
    }
  ],
  "metadata": {}
}
```

### Step 3: User Saves a Version

**Git is the backbone** — every save is a commit with human-readable message.

```
1. User clicks "Save version" in Versions tab
2. Types: "Made hero jump higher"
3. All files staged → git add -A
4. Commit created → git commit -m "Made hero jump higher"
5. Version visible in Versions tab with history
```

**What's in git**:
```
.git/
├── objects/           # Compressed file snapshots
├── refs/              # Branch pointers
└── logs/              # Commit history

$ git log --oneline
abc1234 Made hero jump higher
def5678 Initial platformer setup
```

### Step 4: User Closes App Without Sign-Up

**Everything persists** — it's just files on their computer.

When user closes Creator:
- ✅ All projects in `~/.creator/workspace/` intact
- ✅ All chat history in `~/.creator/conversations/` saved
- ✅ All version history in git objects preserved
- ✅ Settings in `~/.creator/settings.json` remembered

When user reopens Creator:
- ✅ Sidebar loads all projects from `workspace/`
- ✅ Previous conversations can be resumed from `conversations/`
- ✅ Version history fully recoverable
- **No data lost.** No sign-up required.

---

## Where Does Each Thing Get Saved?

| What | Where | Format | Survives Restart? |
|------|-------|--------|-------------------|
| **Project files** | `~/.creator/workspace/{project}/files/` | Actual code files (.py, .java, etc.) | ✅ Yes |
| **Version history** | `~/.creator/workspace/{project}/.git/objects/` | Git objects (compressed) | ✅ Yes |
| **Chat history** | `~/.creator/conversations/{id}.json` | JSON (one per conversation) | ✅ Yes |
| **Project metadata** | `~/.creator/workspace/{project}/project.json` | JSON (name, template, fields) | ✅ Yes |
| **AI provider keys** | `~/.creator/auth.json` | JSON (optional, user's own keys) | ✅ Yes |
| **App settings** | `~/.creator/settings.json` | JSON (theme, window size, etc.) | ✅ Yes |

---

## Project Context Across Workflows

### Example: Long Development Cycle

```
Day 1:
  └─ Create project "DemoApp"
     └─ Ask AI: "Create a login form"
     └─ Save version: "Added login UI"
     └─ Chat history saved in conversations/{id1}.json

Day 2:
  └─ Open Creator again
     └─ Project "DemoApp" appears (from workspace/)
     └─ Previous conversation available (from conversations/)
     └─ Ask AI: "Add password validation"  ← Uses NEW conversation
     └─ Can reference old chat context
     └─ Save version: "Added validation"

Day 7:
  └─ Restore to "Day 1" version
     └─ All files revert (git checkout)
     └─ Chat history from Day 1 still accessible
     └─ Can create new conversation from old version
```

### Multiple Projects, Separate Contexts

```
Project 1: my-game
  ├─ workspace/my-game/files/        ← Code files
  ├─ workspace/my-game/.git/         ← Versions
  └─ conversations/{id1}.json        ← Chat with AI about my-game

Project 2: web-app
  ├─ workspace/web-app/files/        ← Different code files
  ├─ workspace/web-app/.git/         ← Separate versions
  └─ conversations/{id2}.json        ← Chat with AI about web-app

Each project's context is ISOLATED but LINKED
- Conversation stores project_id
- Same AI can chat about multiple projects
- All history preserved independently
```

---

## Context Preservation Over Long Sessions

### Smart Context Windowing (v0.2.0+)

When user has a 1-hour conversation:

```
Hour 0: 10 messages → all fit in provider context limit
Hour 0.5: 20 messages → still fit
Hour 0.9: 40 messages → approaching limit
Hour 1: 50+ messages → EXCEEDS limit

Creator's solution:
  1. Detect: "Too many messages for provider"
  2. Window: "Keep recent 10, summarize older 40"
  3. Send to AI: [SUMMARY] + [recent messages]
  4. AI responds without context loss
  5. Continue conversation seamlessly
```

**Conversation file**:
```json
{
  "id": "abc12345",
  "messages": [
    {"role": "user", "content": "Q1"},
    {"role": "assistant", "content": "A1"},
    // ... 48 more messages ...
    {"role": "user", "content": "Q50"}
  ],
  "created_at": 1723685400.0,
  "last_updated": 1723695400.0  // 1 hour later
}
```

**When sent to AI**:
```
System: You are a helpful assistant...
System: [SUMMARY OF EARLIER CONTEXT]
User Q49: ...
Assistant A49: ...
User Q50: Current question  ← Only recent messages sent
```

Result: **No context loss**, conversation flows naturally for hours.

---

## What About No Internet / Offline Mode?

If user has no internet when they close the app:

```
✅ All projects saved locally         → recoverable
✅ All chat history saved locally     → resumable
✅ All versions saved locally         → restorable
✅ Settings saved locally             → remembered
❌ Can't chat with online AI (but Ollama/LocalAI works)
```

When internet returns:

```
Creator detects internet
└─ Auto-resumes with free providers
   └─ User can chat again without any manual action
```

---

## Storage Locations by Platform

| Platform | Workspace Path |
|----------|---|
| **Windows** | `C:\Users\{username}\.creator\workspace` |
| **macOS** | `/Users/{username}/.creator/workspace` |
| **Linux** | `/home/{username}/.creator/workspace` |

All **hidden** by default (dot-prefix on Unix, attribute on Windows).

---

## Example: User's Actual Disk After 1 Month

```
~/.creator/
├── workspace/
│   ├── my-game/
│   │   ├── project.json (1KB)
│   │   ├── files/ (50MB) 
│   │   └── .git/ (100MB - full history of every change)
│   ├── web-scraper/
│   │   ├── project.json (1KB)
│   │   ├── files/ (5MB)
│   │   └── .git/ (20MB)
│   └── experiments/
│       └── ... (more projects)
│
├── conversations/
│   ├── chat-2026-08-14-game.json (500KB - 100 messages)
│   ├── chat-2026-08-15-scraper.json (200KB - 50 messages)
│   └── ... (one file per conversation thread)
│
├── auth.json (1KB - optional API keys)
└── settings.json (2KB)

Total: ~150-200MB for multiple projects + full history
```

**No cloud upload.** All on user's machine.

---

## The Zero-Sign-Up Promise

| Scenario | What Happens |
|----------|---|
| **User closes app** | ✅ Everything saved locally, reopens seamlessly |
| **User loses internet** | ✅ Projects and history still accessible, can use local models |
| **User never signs up** | ✅ Works perfectly with free AI providers, no payment method needed |
| **User provides API key** | ✅ Hybrid mode: free providers + user's paid key, seamless rotation |
| **User deletes project** | ✅ Can recover from git history (old versions still there) |
| **User runs out of disk space** | ⚠️ Can archive old projects or prune old versions |

---

## Summary: Where It All Saves

```
User ──→ Creates project/chats/saves version
           ↓
         Creator app
           ↓
         All data written to ~/.creator/
           ├─ workspace/       ← Projects + versions (git)
           ├─ conversations/   ← Chat history
           ├─ auth.json        ← API keys (optional)
           └─ settings.json    ← Preferences
           ↓
         User closes app
           ↓
         Data persists on disk
           ↓
         User reopens Creator
           ↓
         Everything loads from ~/.creator/
         No sign-up, no cloud, no loss
```

That's it. **No servers. No subscriptions. No sign-ups. Just local files.**
