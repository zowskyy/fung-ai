# Creator Mobile (Android/iOS) — Roadmap

**Goal**: Use Creator on phone just like ChatGPT app (build things, chat with AI, save locally)  
**Target**: Android first, then iOS  
**Scope**: MVP (not high-scale, just workable)

---

## Architecture: Desktop + Mobile Sync

```
Desktop (Windows/macOS/Linux)
├─ Creator.exe
│  ├─ PySide6 UI
│  └─ Python backend
└─ ~/.creator/
   ├─ workspace/     ← Projects
   ├─ conversations/ ← Chat history
   └─ auth.json      ← Keys

          ↓↑ (WebSocket / Local API)

Mobile App (Android/iOS)
├─ React Native / Flutter UI
├─ Local API client
└─ ~/.creator/ (synced)
   ├─ workspace/
   ├─ conversations/
   └─ auth.json
```

**Key Insight**: Both desktop and mobile read/write to same `~/.creator/` directory. Changes sync automatically.

---

## Option 1: Browser-Based (Simplest, MVP)

**Approach**: Create a web UI for Creator, works on mobile browser

**Pros**:
- ✅ Reuse all backend code (Python)
- ✅ Works on any phone (no app store needed)
- ✅ One codebase for desktop + mobile
- ✅ Easiest to build (~2-3 weeks)

**Cons**:
- ❌ Browser-based (not native feel)
- ❌ Needs to run server locally or on device

**Tech Stack**:
- Frontend: React / Vue.js (responsive web UI)
- Backend: FastAPI (Python REST API)
- Communication: WebSocket (real-time chat)
- Storage: Same `~/.creator/` folder

**Timeline**: 2-3 weeks (fast MVP)

---

## Option 2: React Native (Best Balance)

**Approach**: Single codebase for iOS + Android

**Pros**:
- ✅ Native mobile experience
- ✅ Same code runs on iOS + Android
- ✅ Access to phone APIs (camera, files, notifications)
- ✅ Works offline

**Cons**:
- ⚠️ Requires native modules for some features
- ⚠️ More complex setup (~1 month)

**Tech Stack**:
- Frontend: React Native
- Backend: Reuse Python (via REST API or local subprocess)
- Communication: WebSocket
- Storage: File system (native access)
- Build: Expo (easier) or bare React Native

**Timeline**: 3-4 weeks (medium)

```
creator-mobile/
├─ src/
│  ├─ screens/
│  │  ├─ HomeScreen.tsx      ← Projects list
│  │  ├─ EditorScreen.tsx     ← Code editor
│  │  ├─ AIScreen.tsx         ← Chat with AI
│  │  └─ VersionsScreen.tsx   ← Save/restore
│  ├─ api/
│  │  ├─ projects.ts          ← Project API calls
│  │  ├─ ai.ts                ← AI chat API
│  │  └─ storage.ts           ← Local file access
│  └─ App.tsx
├─ app.json
└─ package.json
```

---

## Option 3: Flutter (Most Native)

**Approach**: Single Dart codebase for iOS + Android

**Pros**:
- ✅ Most native performance
- ✅ Single language (Dart)
- ✅ Excellent UI components
- ✅ Fast compilation

**Cons**:
- ⚠️ Different tech stack (Dart, not JS)
- ⚠️ ~4-5 weeks

**Tech Stack**:
- Frontend: Flutter
- Backend: Python (via local API)
- Communication: gRPC or REST + WebSocket
- Storage: `path_provider` package + file system

**Timeline**: 4-5 weeks (slower)

---

## Recommended: Option 1 (Browser MVP) + Option 2 (React Native Later)

### Phase 1: Web MVP (2-3 weeks)

**Goal**: Get Creator working on phone browser first

**Steps**:

1. **Extract Python Backend to REST API**
   ```python
   # ai/server.py (new)
   from fastapi import FastAPI
   from fastapi.websockets import WebSocket
   
   app = FastAPI()
   
   @app.post("/api/projects")
   async def list_projects():
       return list_projects()
   
   @app.websocket("/ws/chat")
   async def websocket_chat(websocket: WebSocket):
       # Handle AI chat via WebSocket
   
   @app.post("/api/ai/complete")
   async def ai_complete(prompt: str):
       return cycling_backend.complete(...)
   ```

2. **Create Web UI** (React)
   ```
   creator-web/
   ├─ src/
   │  ├─ pages/
   │  │  ├─ Projects.tsx
   │  │  ├─ Editor.tsx
   │  │  ├─ Chat.tsx
   │  │  └─ Versions.tsx
   │  └─ App.tsx
   ├─ package.json
   └─ Dockerfile (optional)
   ```

3. **Mobile-Responsive Design**
   - Tailwind CSS for responsive layouts
   - Touch-friendly buttons (48px+ tap targets)
   - Bottom navigation on mobile
   - Single-column layout on narrow screens

4. **Run Locally**
   ```bash
   # Desktop: Start API server
   python ai/server.py  # Runs on localhost:8000
   
   # Phone: Open browser
   http://192.168.1.100:8000
   ```

**Result**: Creator works on phone browser, 70% feature parity with desktop

---

### Phase 2: React Native (3-4 weeks, after Phase 1)

**Goal**: Native mobile app (better performance, offline, app store)

**Setup**:
```bash
npx create-expo-app creator-mobile
cd creator-mobile
npm install @react-navigation/native @react-native-async-storage/async-storage
```

**Architecture**:
```
creator-mobile/
├─ src/
│  ├─ api/
│  │  ├─ ProjectsAPI.ts       ← Call /api/projects
│  │  ├─ AiAPI.ts             ← WebSocket to /ws/chat
│  │  └─ StorageAPI.ts        ← Local file system
│  ├─ screens/
│  │  ├─ HomeScreen.tsx       ← Project list
│  │  ├─ EditorScreen.tsx     ← Code editor (Monaco)
│  │  ├─ AIScreen.tsx         ← Chat
│  │  └─ VersionsScreen.tsx   ← Versions
│  ├─ components/
│  │  ├─ ProjectCard.tsx
│  │  ├─ ChatBubble.tsx
│  │  ├─ VersionTimeline.tsx
│  │  └─ CodeEditor.tsx
│  └─ App.tsx
├─ android/ (auto-generated)
├─ ios/ (auto-generated)
├─ app.json
└─ package.json
```

**Key Libraries**:
- `@react-navigation/native` — screen navigation
- `@react-native-async-storage/async-storage` — local storage
- `react-native-file-access` — file system access
- `react-native-webview` — embed code editor

---

## Feature Parity: Desktop vs Mobile

| Feature | Desktop | Web MVP | React Native |
|---------|---------|---------|--------------|
| **Create project** | ✅ | ✅ | ✅ |
| **Edit code** | ✅ | ✅ (limited) | ✅ |
| **Chat with AI** | ✅ | ✅ | ✅ |
| **Save version** | ✅ | ✅ | ✅ |
| **Restore version** | ✅ | ✅ | ✅ |
| **Run project** | ✅ | ❌ (needs desktop) | ❌ (needs desktop) |
| **Offline mode** | ✅ | ⚠️ (partial) | ✅ |
| **App store** | ❌ | N/A | ✅ |

---

## Data Sync: Desktop ↔ Mobile

Both read/write to `~/.creator/`:

```
Desktop changes project
  ↓
Writes to ~/.creator/workspace/my-game/files/
  ↓
Mobile app polls ~/creator/workspace/ every 5s
  ↓
Detects changes, refreshes UI

Mobile saves chat
  ↓
Writes to ~/.creator/conversations/
  ↓
Desktop app refreshes conversation list
```

**Automatic sync** — no manual upload/download needed.

---

## Quick Start (Web MVP)

### Step 1: Create API Server

**File: `ai/server.py`**
```python
from fastapi import FastAPI, WebSocket
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import json
from pathlib import Path

app = FastAPI()

# Enable CORS for mobile
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve web UI
app.mount("/", StaticFiles(directory="web/build", html=True), name="web")

@app.get("/api/projects")
async def list_projects():
    from sandbox.workspace import list_projects
    ws = Path.home() / ".creator" / "workspace"
    projects = list_projects(ws)
    return [
        {
            "id": p.root.name,
            "name": p.name,
            "template": p.data.get("template"),
            "created": p.data.get("created"),
        }
        for p in projects
    ]

@app.get("/api/projects/{project_id}/conversations")
async def list_conversations(project_id: str):
    from ai.context_manager import ConversationPersistence
    persistence = ConversationPersistence()
    convs = persistence.list_conversations()
    return [
        {
            "id": c.id,
            "project_id": c.project_id,
            "last_message": c.messages[-1].content if c.messages else "",
            "updated": c.last_updated,
        }
        for c in convs
        if c.project_id == project_id
    ]

@app.websocket("/ws/chat/{project_id}/{conversation_id}")
async def websocket_chat(websocket: WebSocket, project_id: str, conversation_id: str):
    await websocket.accept()
    from ai import get_backend
    backend = get_backend()
    
    # Resume or start conversation
    backend.start_conversation(conversation_id)
    
    try:
        while True:
            data = await websocket.receive_json()
            if data.get("type") == "message":
                response = backend.complete(
                    system=data.get("system", ""),
                    messages=data.get("messages", []),
                )
                await websocket.send_json({"type": "response", "content": response})
    except Exception as e:
        await websocket.send_json({"type": "error", "error": str(e)})
    finally:
        await websocket.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### Step 2: Create Web UI (React)

**File: `web/src/App.tsx`**
```typescript
import React, { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import ProjectList from './pages/ProjectList';
import Editor from './pages/Editor';
import './App.css';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<ProjectList />} />
        <Route path="/project/:id" element={<Editor />} />
      </Routes>
    </BrowserRouter>
  );
}
```

### Step 3: Run

```bash
# Terminal 1: Start API
python ai/server.py

# Terminal 2: Start web UI (if needed)
cd web && npm start

# Browser/Phone: Navigate to
http://localhost:8000  # Or phone IP
```

---

## Implementation Phases

### Phase 1: Web MVP (Weeks 1-3)
- [ ] Extract FastAPI backend from PySide6 app
- [ ] Build React web UI (responsive)
- [ ] WebSocket chat integration
- [ ] Test on phone browser
- [ ] Deploy (optional: cloud, or just localhost)

### Phase 2: React Native (Weeks 4-7)
- [ ] Setup React Native + Expo
- [ ] Rewrite screens for mobile (native components)
- [ ] File system access (project files)
- [ ] Offline support (sync when online)
- [ ] Build APK for Android
- [ ] Test on real phone

### Phase 3: App Store (Week 8+)
- [ ] Google Play Console account
- [ ] App signing + submission
- [ ] Marketing assets
- [ ] Publish to Play Store

---

## Estimated Effort

| Option | Effort | Timeline | Quality |
|--------|--------|----------|---------|
| Web MVP | 40 hours | 2-3 weeks | 🟡 Good |
| React Native | 80 hours | 4-5 weeks | 🟢 Excellent |
| Full Solution | 120 hours | 6-8 weeks | 🟢 Excellent |

---

## My Recommendation

**Start with Web MVP** (Phase 1):
- ✅ Reuse all backend code (Python)
- ✅ Works today (FastAPI + React)
- ✅ Tests on phone browser (no app needed)
- ✅ Can iterate quickly

**Then** (optional) **add React Native** (Phase 2):
- For better UX, app store, offline
- But MVP gets you 70% there in 3 weeks

---

## Files to Create/Modify

**New**:
- `ai/server.py` — FastAPI REST API
- `web/` — React UI folder structure
- `web/src/App.tsx` — Main React app
- `web/src/pages/ProjectList.tsx`
- `web/src/pages/Editor.tsx`
- `web/src/pages/Chat.tsx`
- `web/package.json`

**Modified**:
- `ai/__init__.py` — Export `get_backend()` for server
- `app/utils.py` — Helper functions for storage paths

**No changes needed to**:
- Core Python backend (cycling, persistence, projects)
- `~/.creator/` storage (both desktop and mobile use same)

---

## Next Steps

1. **Decide**: Web MVP or straight to React Native?
2. **Start**: Create `ai/server.py` with FastAPI
3. **Build**: React web UI with responsive design
4. **Test**: On phone browser (USB tether or local network)

Want me to start building the Web MVP?
