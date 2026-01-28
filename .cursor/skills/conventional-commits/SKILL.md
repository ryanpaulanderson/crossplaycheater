---
name: conventional-commits
description: Generate commit messages following the Conventional Commits specification. Use when committing code, creating git commits, or when the user asks about commit message format.
---

# Conventional Commits

Follow the [Conventional Commits](https://www.conventionalcommits.org/) specification when writing commit messages.

## Format

```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

## Types

| Type | Description |
|------|-------------|
| `feat` | New feature |
| `fix` | Bug fix |
| `docs` | Documentation only |
| `style` | Formatting, missing semicolons, etc. (no code change) |
| `refactor` | Code change that neither fixes a bug nor adds a feature |
| `test` | Adding or updating tests |
| `chore` | Maintenance tasks, dependency updates, build changes |

## Rules

1. **Type is required** - Always start with a valid type
2. **Scope is optional** - Use parentheses: `feat(auth): add login`
3. **Description is required** - Lowercase, no period, imperative mood
4. **Breaking changes** - Add `!` after type/scope: `feat!: remove deprecated API`
5. **Body** - Explain "what" and "why", not "how"
6. **Footer** - Reference issues: `Fixes #123` or `BREAKING CHANGE: description`

## Examples

**Simple feature:**
```
feat: add user profile page
```

**Feature with scope:**
```
feat(api): add endpoint for user preferences
```

**Bug fix with body:**
```
fix(auth): prevent session timeout during active use

The session was expiring even when the user was actively
interacting with the application. Now activity resets the
timeout timer.
```

**Breaking change:**
```
feat(api)!: change authentication to use JWT tokens

BREAKING CHANGE: API now requires Bearer token instead of
API key in the Authorization header.
```

**Documentation:**
```
docs: update installation instructions for Windows
```

**Chore:**
```
chore: upgrade numpy to 2.0.0
```

## Commit Message Best Practices

- Keep the subject line under 72 characters
- Use imperative mood ("add" not "added" or "adds")
- Don't capitalize the first letter after the colon
- No period at the end of the subject line
- Separate subject from body with a blank line
- Wrap body at 72 characters
