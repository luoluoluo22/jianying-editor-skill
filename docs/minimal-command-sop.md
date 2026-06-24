# Minimal Command SOP

Use this SOP for simple editing requests to minimize noisy exploration.

## Goal

- Produce one runnable script
- Run once
- Validate result with fixed checks

## Step 1: Minimal Environment Check (2 commands max)

### macOS
```bash
python3 --version
ls ~/Movies/JianyingPro/User\ Data/Projects/com.lveditor.draft 2>/dev/null || \
  ls ~/Movies/JianyingPro\ Drafts/ 2>/dev/null || \
  echo "Draft path not found"
```

### Windows
```powershell
python --version
Test-Path "C:\Users\Administrator\AppData\Local\JianyingPro\User Data\Projects\com.lveditor.draft"
```

If draft path differs, set `JY_PROJECTS_ROOT` and continue.

## Step 2: Asset Check (1 command)

### macOS
```bash
ls .agents/skills/jianying-editor/assets/ 2>/dev/null || \
  ls .agent/skills/jianying-editor/assets/
```

### Windows
```powershell
Get-ChildItem .agent\skills\jianying-editor\assets -File
```

Do not recursively scan the whole workspace unless asset lookup fails.

## Step 3: Script Generation

- Create exactly one script in workspace root, e.g. `simple_edit.py`.
- Use deterministic APIs only:
  - `JyProject(...)`
  - `add_media_safe(...)`
  - `add_cloud_media(...)` or `add_cloud_music(...)`
  - `add_text_simple(...)` / `add_narrated_subtitles(...)`
  - `save()`

## Step 4: Single Execution

```bash
python simple_edit.py
```

If failed, patch script once based on the concrete error, then rerun once.

## Step 5: Acceptance Validation (Mandatory)

Verify all:

- Draft directory exists
- Save success log appears
- At least one video segment exists
- BGM is on audio track (if used)
- Subtitles exist when narration exists

## Error Handling Rules

- `SegmentOverlap`: move clip start to track end or separate track.
- Missing asset: switch to known local asset or valid cloud ID.
- Import/path failure: set `JY_SKILL_ROOT`, rerun bootstrap.

## Anti-Patterns (Avoid)

- Repeated recursive directory scanning over full workspace
- Temporary introspection files (`*_dir.txt`, `output.txt`) unless debugging is explicitly requested
- Multiple style/effect searches before first successful draft generation
