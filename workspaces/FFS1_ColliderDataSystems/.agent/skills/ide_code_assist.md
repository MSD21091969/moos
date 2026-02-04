# IDE Code Assist Skill

> Primary skill for FILESYST domain (App X).

## Name

ide_code_assist

## Description

Provides code assistance within IDE context, including code completion, refactoring suggestions, and documentation lookup.

## Inputs

- `code_context`: Current code buffer content
- `cursor_position`: Line and column of cursor
- `file_path`: Active file path
- `workspace_root`: Workspace root path

## Outputs

- `suggestions`: List of code suggestions
- `documentation`: Relevant documentation
- `actions`: Available code actions

## Steps

1. Analyze code context around cursor
2. Identify language and framework
3. Generate relevant suggestions
4. Provide documentation links
