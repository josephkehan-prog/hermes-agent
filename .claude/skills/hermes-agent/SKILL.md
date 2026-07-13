```markdown
# hermes-agent Development Patterns

> Auto-generated skill from repository analysis

## Overview
This skill teaches you the core development patterns and conventions used in the `hermes-agent` TypeScript codebase. You'll learn how to structure files, write imports/exports, follow commit message conventions, and understand the project's approach to testing. This guide ensures consistency and maintainability across contributions.

## Coding Conventions

### File Naming
- Use **kebab-case** for all file names.
  - **Example:**  
    ```
    my-feature-file.ts
    hermes-agent-core.ts
    ```

### Import Style
- Use **relative imports** for referencing other files or modules within the project.
  - **Example:**
    ```typescript
    import myUtil from './utils/my-util';
    import config from '../config';
    ```

### Export Style
- Use **default exports** for modules.
  - **Example:**
    ```typescript
    // In my-feature.ts
    const myFeature = () => { /* ... */ };
    export default myFeature;
    ```

### Commit Messages
- Follow **Conventional Commits**.
- Use prefixes like `chore` and `fix`.
- Keep commit messages concise (average ~63 characters).
  - **Examples:**
    ```
    chore: update dependencies
    fix: handle null values in agent response
    ```

## Workflows

### Code Contribution
**Trigger:** When adding or updating code  
**Command:** `/contribute`

1. Create a new file using kebab-case naming.
2. Write code using relative imports and default exports.
3. Add or update tests in a corresponding `.test.ts` file.
4. Commit changes using a conventional commit message (e.g., `fix: ...` or `chore: ...`).
5. Open a pull request for review.

### Dependency Update
**Trigger:** When dependencies need to be updated  
**Command:** `/update-deps`

1. Run your package manager to update dependencies (e.g., `npm update`).
2. Test the application to ensure compatibility.
3. Commit with a message like `chore: update dependencies`.
4. Push and open a pull request if required.

## Testing Patterns

- Test files follow the pattern `*.test.*` (e.g., `agent.test.ts`).
- The specific testing framework is **unknown**; check existing test files for clues.
- Place tests alongside or near the code they test.
- Example test file name:
  ```
  hermes-agent.test.ts
  ```

## Commands
| Command         | Purpose                                      |
|-----------------|----------------------------------------------|
| /contribute     | Steps for contributing code changes           |
| /update-deps    | Steps for updating project dependencies       |
```
