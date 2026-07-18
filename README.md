# Branchoria Hub Site

Static non-UFO knowledge-network hub for `branchoria.com`.

Routes included:

- `/`
- `/privacy-policy/`
- `/terms/`
- `/contact/`
- `/disclosure/`
- `/credits/`

The generated subdomain footers link to the hub policy pages, including the affiliate and AI-assisted content disclosure. The credits page collects reusable asset attributions for maps, icons, emoji graphics, and related publishing resources.

## Approved Site Directory

The home page contains a marker-bounded directory generated from the shared
two-network site registry. Start from `config/network_sites.example.json`, retain only
real public entries, and mark a site with both `"approved": true` and
`"status": "published"` before it can appear. Branchoria entries also use
`"network": "branchoria"`:

```powershell
.\.venv\Scripts\python.exe scripts\build_branchoria_hub_directory.py `
  --registry config\network_sites.json --network branchoria
```

Use `--check` in validation/CI to report drift without changing the hub. The
builder rejects malformed public URLs and duplicate approved IDs or URLs. It
does not publish the hub, edit DNS, infer approval from a completed workflow,
or add draft/failed sites.

The queue worker can perform the same local shared-registry upsert and directory
render after successful jobs when `PHX_QUEUE_HUB_AUTO_REFRESH_ENABLED=1` and the
individual row explicitly supplies `hub_approved=true` and public card copy.
This remains a source refresh only; publishing the hub is a separate operation.
