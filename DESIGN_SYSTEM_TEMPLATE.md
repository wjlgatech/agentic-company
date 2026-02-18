# Design System Template

**Purpose**: Codify design decisions to automate 70% of design choices
**Last Updated**: [DATE]
**Platform**: [Your platform - Web/Mobile/Desktop/AR-VR]

---

## How to Use This Template

1. **Copy this file** to your project root as `DESIGN_SYSTEM.md`
2. **Fill in the bracketed sections** with your project's values
3. **Delete examples** that don't apply to your domain
4. **Add new sections** as you discover repeated design decisions
5. **Update regularly** when design patterns change

**Goal**: Enable Claude (or any AI assistant) to make 70% of design decisions automatically by checking this document.

---

## Core Principles

### 1. [Principle Name - e.g., "Accessibility First"]
**What it means**: [Brief description]
**Tradeoffs**: [What you're giving up for this principle]
**Examples**:
- ✅ Good: [Example of following principle]
- ❌ Bad: [Example of violating principle]

### 2. [Principle Name - e.g., "Mobile-First Design"]
**What it means**: [Brief description]
**Tradeoffs**: [What you're giving up]
**Examples**:
- ✅ Good: [Example]
- ❌ Bad: [Example]

### 3. [Principle Name - e.g., "Performance Over Polish"]
**What it means**: [Brief description]
**Tradeoffs**: [What you're giving up]
**Examples**:
- ✅ Good: [Example]
- ❌ Bad: [Example]

---

## Color Palette

### Primary Colors
| Color Name | Hex | Usage | Reasoning |
|------------|-----|-------|-----------|
| [Primary] | #000000 | [When to use] | [Why this color] |
| [Secondary] | #000000 | [When to use] | [Why this color] |
| [Accent] | #000000 | [When to use] | [Why this color] |

### Semantic Colors
| Semantic | Hex | Usage | Contrast Ratio |
|----------|-----|-------|----------------|
| Error | #FF0000 | Error messages, dangerous actions | [e.g., 4.5:1 on white] |
| Warning | #FFA500 | Warnings, cautions | [e.g., 4.5:1 on white] |
| Success | #00FF00 | Success states, confirmations | [e.g., 4.5:1 on white] |
| Info | #0000FF | Informational messages | [e.g., 4.5:1 on white] |

### Background Considerations
- **Context**: [Where these colors will appear - e.g., light theme only, dark mode support]
- **Accessibility**: [Minimum contrast ratios to maintain]
- **Platform-specific**: [Any platform limitations]

---

## Typography

### Font Stack
```
Primary: [Your primary font]
Fallback: [System fonts or web-safe alternatives]
```

### Type Scale
| Level | Size | Weight | Line Height | Usage |
|-------|------|--------|-------------|-------|
| Heading 1 | [e.g., 32px] | [e.g., Bold] | [e.g., 1.2] | [When to use] |
| Heading 2 | [e.g., 24px] | [e.g., Semibold] | [e.g., 1.3] | [When to use] |
| Body | [e.g., 16px] | [e.g., Regular] | [e.g., 1.5] | [When to use] |
| Small | [e.g., 14px] | [e.g., Regular] | [e.g., 1.4] | [When to use] |
| Caption | [e.g., 12px] | [e.g., Regular] | [e.g., 1.3] | [When to use] |

### Platform-Specific Rules
- **Minimum readable size**: [e.g., 14px on mobile]
- **Maximum line length**: [e.g., 70 characters for readability]
- **Special considerations**: [e.g., high DPI, touch targets]

---

## Sizing System

### Base Units
- Base unit: [e.g., 8px] - All spacing/sizing should be multiples of this
- Scaling factor: [e.g., 1.5x or 2x for larger breakpoints]

### Size Scale
| Name | Value | Usage |
|------|-------|-------|
| xs | [e.g., 4px] | [When to use] |
| sm | [e.g., 8px] | [When to use] |
| md | [e.g., 16px] | [When to use] |
| lg | [e.g., 32px] | [When to use] |
| xl | [e.g., 64px] | [When to use] |

### Interactive Element Sizing
| Element | Min Width | Min Height | Reasoning |
|---------|-----------|------------|-----------|
| Button | [e.g., 44px] | [e.g., 44px] | [e.g., Touch target size (iOS HIG)] |
| Input Field | [e.g., 200px] | [e.g., 44px] | [Reasoning] |
| Card | [e.g., 280px] | [e.g., auto] | [Reasoning] |

---

## Spacing System

### Base Unit
- Base: [e.g., 8px] - All spacing should be multiples

### Spacing Scale
| Name | Value | Usage |
|------|-------|-------|
| xs | [e.g., 4px] | [When to use - e.g., tight spacing] |
| sm | [e.g., 8px] | [When to use - e.g., between related elements] |
| md | [e.g., 16px] | [When to use - e.g., between sections] |
| lg | [e.g., 32px] | [When to use - e.g., major sections] |
| xl | [e.g., 64px] | [When to use - e.g., page margins] |

### Component-Specific Spacing
- **Card padding**: [e.g., 16px internal padding]
- **Section margins**: [e.g., 32px vertical, 24px horizontal]
- **List item spacing**: [e.g., 8px between items]

---

## Layout Patterns

### Pattern 1: [Pattern Name - e.g., "Hero Section"]
**When to use**: [Description of use case]
**Structure**:
```
[Layout structure - e.g., pseudo-code or description]
- Container: [specs]
- Content: [specs]
- Actions: [specs]
```

### Pattern 2: [Pattern Name - e.g., "Card Grid"]
**When to use**: [Description]
**Structure**:
```
[Layout structure]
```

### Pattern 3: [Pattern Name - e.g., "Sidebar + Content"]
**When to use**: [Description]
**Structure**:
```
[Layout structure]
```

---

## Component Guidelines

### Buttons
**Primary Button**:
- Size: [e.g., 44px height]
- Color: [e.g., Primary color]
- Text: [e.g., 16px, white]
- States: Default, Hover, Active, Disabled

**Secondary Button**:
- Size: [Same as primary]
- Color: [e.g., Transparent with border]
- Text: [e.g., 16px, primary color]
- States: Default, Hover, Active, Disabled

### Alerts/Notifications

**Error Alert**:
- Background: [e.g., Error red]
- Text: [e.g., White, 16px]
- Icon: [e.g., ⚠️]
- Auto-dismiss: [e.g., No - user must acknowledge]

**Success Alert**:
- Background: [e.g., Success green]
- Text: [e.g., Black, 16px]
- Icon: [e.g., ✓]
- Auto-dismiss: [e.g., Yes - 3 seconds]

### [Your Custom Components]
**[Component Name]**:
- [Specifications]

---

## Animation Guidelines

### Timing
- **Fast**: [e.g., 100-200ms] - [When to use]
- **Medium**: [e.g., 200-300ms] - [When to use]
- **Slow**: [e.g., 300-500ms] - [When to use]
- **Maximum**: [e.g., 500ms] - Anything longer feels sluggish

### Easing
- **Default**: [e.g., ease-in-out] - [Description]
- **Enter**: [e.g., ease-out] - [Description]
- **Exit**: [e.g., ease-in] - [Description]

### Animation Constraints
**NEVER Use**:
- ❌ [Anti-pattern 1 - e.g., Rapid flashing (seizure risk)]
- ❌ [Anti-pattern 2 - e.g., Sudden jumps (jarring)]
- ❌ [Anti-pattern 3]

**ALWAYS Prefer**:
- ✅ [Good pattern 1 - e.g., Smooth fades]
- ✅ [Good pattern 2 - e.g., Gentle scaling]
- ✅ [Good pattern 3]

---

## Accessibility Requirements

### WCAG Compliance Level: [AA or AAA]

**Color Contrast**:
- Text on background: **Minimum [e.g., 4.5:1]**
- UI components: **Minimum [e.g., 3:1]**
- Large text (>24px): **Minimum [e.g., 3:1]**

**Interaction**:
- Touch targets: **Minimum [e.g., 44x44px]**
- Focus indicators: **Visible [e.g., 2px outline]**
- Keyboard navigation: All interactive elements accessible

**Content**:
- Alt text: Required for all images
- Form labels: Required for all inputs
- Error messages: Include specific instructions

### Platform-Specific Accessibility
- [Platform 1 requirements]
- [Platform 2 requirements]

---

## Platform-Specific Considerations

### [Platform Name - e.g., iOS]
- [Consideration 1]
- [Consideration 2]
- [Consideration 3]

### [Platform Name - e.g., Android]
- [Consideration 1]
- [Consideration 2]

### Performance Budgets
- [Budget 1 - e.g., Page load time < 2s]
- [Budget 2 - e.g., Maximum bundle size 200KB]
- [Budget 3 - e.g., 60fps animations]

---

## Automated Validation

### Design Linting (Optional but Recommended)

If using code-based validation:

```javascript
// Example validation function (adapt to your stack)
function validateDesign(component) {
  const issues = [];

  // Size validation
  if (component.size < MIN_SIZE) {
    issues.push(`Too small: ${component.size}px < ${MIN_SIZE}px`);
  }

  // Contrast validation
  const contrast = calculateContrast(component.fg, component.bg);
  if (contrast < MIN_CONTRAST) {
    issues.push(`Contrast ${contrast}:1 < required ${MIN_CONTRAST}:1`);
  }

  // [Add your validation rules]

  return issues;
}
```

### CI/CD Integration (Optional)

```bash
# Example pre-commit hook
npm run design-lint
# Or: python scripts/validate_design.py
```

---

## Decision Tree

When creating a new component:

```
1. Is it interactive?
   ├─ YES → Minimum [size], ensure focus state
   └─ NO → Continue to step 2

2. Does it convey status/state?
   ├─ YES → Use semantic colors (error/warning/success)
   └─ NO → Continue to step 3

3. Is it reusable?
   ├─ YES → Create as component, add to design system
   └─ NO → Use inline styles, document if pattern repeats

4. Check automated validation
   └─ Run validateDesign() - must pass all checks
```

---

## Examples Gallery

### Good Examples

**1. [Example Name]**
- Why it's good: [Explanation]
- Rules applied: [Which design system rules]

**2. [Example Name]**
- Why it's good: [Explanation]
- Rules applied: [Which design system rules]

### Bad Examples (Anti-Patterns)

**1. ❌ [Anti-Pattern Name]**
- Why it's bad: [Explanation]
- Rules violated: [Which design system rules]
- How to fix: [Correction]

**2. ❌ [Anti-Pattern Name]**
- Why it's bad: [Explanation]
- Rules violated: [Which design system rules]
- How to fix: [Correction]

---

## Maintenance Log

| Date | Change | Reason | Updated By |
|------|--------|--------|------------|
| [DATE] | Initial creation | Establish design standards | [Name] |

---

## When to Escalate to Human

Claude (or any AI assistant) should ask user for guidance when:

1. **Novel component not covered**: New UI pattern not in existing guidelines
2. **Conflicting rules**: Rules that contradict each other for a specific case
3. **Aesthetic judgment beyond rules**: Subjective decisions requiring taste
4. **Brand/identity decisions**: Decisions affecting product personality
5. **Accessibility trade-off**: Rule compliance vs UX (should never sacrifice accessibility, but ask if unsure)

---

## Quick Reference Card

**Most Common Decisions**:
- Error color? → [Your error color]
- Success color? → [Your success color]
- Minimum touch target? → [Your minimum size]
- Minimum text size? → [Your minimum text size]
- Spacing between elements? → [Your spacing scale]
- Animation duration? → [Your timing]
- Contrast ratio? → [Your minimum contrast]

**Most Common Violations**:
- [Violation 1 - e.g., Touch target too small]
- [Violation 2 - e.g., Contrast too low]
- [Violation 3 - e.g., Text too small]
- [Violation 4 - e.g., Inconsistent spacing]

---

**Document Version**: 1.0
**Last Updated**: [DATE]
**Applicable To**: [Your Project Name]
