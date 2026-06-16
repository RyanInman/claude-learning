#!/usr/bin/env bash
# discover.sh - emit a compact Repo Profile for the extract-patterns skill.
#
# Runs all of Step 1 discovery deterministically and prints distilled signal,
# keeping raw listings (git ls-files, extension histograms) out of the model's
# context. The model reads this profile and classifies layout/stack; it does not
# re-run the mechanical scans by hand.
#
# Usage: discover.sh [PROJECT_ROOT]   (defaults to the current directory)

set -uo pipefail

ROOT="${1:-$PWD}"
cd "$ROOT" 2>/dev/null || { echo "ERROR: cannot cd into $ROOT"; exit 1; }

if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  VCS="git"
  FILES="$(git ls-files)"
else
  VCS="none"
  FILES="$(find . -type d \
      \( -name node_modules -o -name .git -o -name dist -o -name build \
         -o -name target -o -name vendor -o -name __pycache__ -o -name .venv \) -prune \
      -o -type f -print | sed 's|^\./||')"
fi

count="$(printf '%s\n' "$FILES" | grep -c . )"

echo "=== REPO PROFILE ==="
echo "Root: $ROOT"
echo "VCS: $VCS"
echo "Files: $count"
echo

echo "--- Directory skeleton (top 2 levels) ---"
printf '%s\n' "$FILES" | awk -F/ '{print $1 (NF>1 ? "/"$2 : "")}' | sort -u | head -60
echo

echo "--- Top file extensions ---"
printf '%s\n' "$FILES" | sed -n 's/.*\.\([A-Za-z0-9_]*\)$/\1/p' | sort | uniq -c | sort -rn | head -15
echo

echo "--- Root manifests / lockfiles / toolchain ---"
ls -1 package.json package-lock.json pnpm-lock.yaml yarn.lock tsconfig.json \
      pyproject.toml requirements.txt Pipfile poetry.lock setup.py \
      go.mod go.sum Cargo.toml Cargo.lock Gemfile Gemfile.lock \
      pom.xml build.gradle build.gradle.kts settings.gradle \
      composer.json composer.lock mix.exs mix.lock \
      Package.swift pubspec.yaml Makefile Dockerfile 2>/dev/null | head -30
echo

echo "--- Detected ecosystems ---"
detect() { printf '%s\n' "$FILES" | grep -Eq "$1" && echo "$2"; }
{
  detect '(^|/)(package\.json|pnpm-lock\.yaml|yarn\.lock|tsconfig\.json)$' 'Node / JS / TS'
  detect '(^|/)(pyproject\.toml|requirements\.txt|Pipfile|poetry\.lock|setup\.py)$' 'Python'
  detect '(^|/)go\.mod$' 'Go'
  detect '(^|/)Cargo\.toml$' 'Rust'
  detect '(^|/)(Gemfile|.*\.gemspec)$' 'Ruby'
  detect '(^|/)(pom\.xml|build\.gradle(\.kts)?|settings\.gradle)$' 'JVM (Java / Kotlin)'
  detect '(^|/)(.*\.csproj|.*\.sln|.*\.fsproj|packages\.config)$' '.NET'
  detect '(^|/)composer\.json$' 'PHP'
  detect '(^|/)mix\.exs$' 'Elixir'
  detect '(^|/)(Package\.swift|.*\.xcodeproj|Podfile)$' 'Swift'
  detect '(^|/)pubspec\.yaml$' 'Dart / Flutter'
} | sort -u
echo

echo "--- Sub-project manifests (in subdirectories) ---"
printf '%s\n' "$FILES" | grep -E '/(package\.json|pyproject\.toml|go\.mod|Cargo\.toml|Gemfile|pom\.xml|composer\.json|mix\.exs|pubspec\.yaml)$' | head -40
echo

echo "--- Workspace markers ---"
ls -1 pnpm-workspace.yaml turbo.json lerna.json nx.json go.work 2>/dev/null | head
grep -lE '^[[:space:]]*(\[workspace\]|"workspaces")' Cargo.toml package.json 2>/dev/null | head
echo

echo "--- Existing docs (headings) ---"
grep -RHn '^#' CLAUDE.md README* agent_docs/*.md docs/*.md 2>/dev/null | head -60
echo

echo "=== END PROFILE ==="
