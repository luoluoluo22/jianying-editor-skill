# CLI API Contract

## Common Output Contract (`--json`)

All upgraded scripts return:

```json
{
  "ok": true,
  "code": "ok",
  "reason": "",
  "data": {}
}
```

## Exit Codes

- `0`: success
- `1`: runtime/infra failure
- `2`: invalid input or strict precondition failure

## Scripts

### `scripts/api_validator.py`
- `--project`
- `--video`
- `--strict`
- `--json`

### `scripts/asset_search.py`
- positional `query`
- `-c/--category`
- `-l/--limit`
- `--list`
- `--json`

### `scripts/build_cloud_music_library.py`
- `--projects-root`
- `--music-csv`
- `--sfx-csv`
- `--dry-run`
- `--json`

### `scripts/auto_exporter.py`
- positional `name output`
- `--res`
- `--fps`
- `--json`
