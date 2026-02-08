# Documentation Templates

This directory contains templates for creating consistent documentation across FFS applications.

## Available Templates

### 1. index_template.md
**Purpose**: Template for the main `.agent/index.md` file in each application.

**Usage**: Copy and replace placeholders:
- `[APP_NAME]` - Application name (e.g., "FFS4 Sidepanel Browser")
- `[FULL_PATH_TO_APP]` - Full path to the application directory
- `[One sentence description]` - Brief description
- Fill in all sections with app-specific details

**Key Sections**:
- Hierarchy and location
- Purpose and responsibilities
- Key components
- Integration points
- Development setup

### 2. codebase_template.md
**Purpose**: Template for detailed technical documentation in `knowledge/codebase.md`.

**Usage**: Copy and fill in:
- Architecture and implementation details
- Directory structure
- Component descriptions
- Data flow patterns
- API integration details
- Testing approach

**Key Sections**:
- Component architecture
- State management
- API & integration patterns
- Performance considerations
- Testing strategy

### 3. instructions_template.md
**Purpose**: Template for development guidelines in `instructions/[feature].md`.

**Usage**: Create feature-specific instructions:
- Copy template to `instructions/` directory
- Name file based on feature area
- Fill in app-specific patterns and guidelines
- Include code examples relevant to your app

**Key Sections**:
- Code organization patterns
- Common patterns and anti-patterns
- Integration guidelines
- Testing guidelines
- Debugging tips

## Using These Templates

### For New Applications

1. **Create .agent structure**:
   ```bash
   mkdir -p [APP_DIR]/.agent/{configs,instructions,knowledge,rules,skills,tools,workflows}
   ```

2. **Copy and customize index.md**:
   ```bash
   cp index_template.md [APP_DIR]/.agent/index.md
   # Edit and replace placeholders
   ```

3. **Copy and customize codebase.md**:
   ```bash
   cp codebase_template.md [APP_DIR]/.agent/knowledge/codebase.md
   # Fill in technical details
   ```

4. **Create instruction files as needed**:
   ```bash
   cp instructions_template.md [APP_DIR]/.agent/instructions/feature_development.md
   # Customize for specific feature areas
   ```

### For Existing Applications

1. **Review current documentation**
2. **Identify missing sections** using templates as checklist
3. **Fill in gaps** following template structure
4. **Keep what works**, don't force template structure if current docs are better

## Template Customization Guidelines

### Placeholders to Replace

All templates use these placeholders:
- `[APP_NAME]` - Full application name
- `[APP_DIRECTORY]` - Directory name
- `[FULL_PATH_TO_APP]` - Absolute path
- `[One sentence description]` - Brief description
- `[Feature Name]` - Specific feature being documented
- `[ComponentName]` - Actual component name

### What to Keep

- Section headings (adjust if needed)
- Code block examples (replace with real code)
- Checklists
- Standard patterns

### What to Remove

- Sections that don't apply to your app
- Placeholder text
- Examples that aren't relevant

### What to Add

- App-specific sections
- Additional examples
- Links to related documentation
- Team-specific conventions

## Best Practices

1. **Be Specific**: Replace generic examples with real code from your app
2. **Be Concise**: Remove sections that don't add value
3. **Be Current**: Keep documentation up-to-date as code changes
4. **Be Helpful**: Write for your future self and new team members
5. **Link Liberally**: Reference related docs, not duplicate content

## Examples

See FFS4-8 for completed examples using these templates:
- FFS4_application00_ColliderSidepanelAppnodeBrowser
- FFS5_application01_ColliderPictureInPictureMainAgentSeat
- FFS6_applicationx_FILESYST_ColliderIDE_appnodes
- FFS7_applicationz_ADMIN_ColliderAccount_appnodes
- FFS8_application1_CLOUD_my-tiny-data-collider_appnodes
