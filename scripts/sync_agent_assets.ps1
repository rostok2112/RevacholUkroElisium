# Copies project skills into local Codex/Claude directories.
# Review paths before running.

param(
  [string]$CodexHome = "$env:USERPROFILE\.codex",
  [string]$ClaudeHome = "$env:USERPROFILE\.claude"
)

Write-Host "Project skills are already stored in .agents/skills and .claude/skills."
Write-Host "If your Codex build requires global install, copy .agents/skills/* to $CodexHome\skills manually or via your skill installer."
