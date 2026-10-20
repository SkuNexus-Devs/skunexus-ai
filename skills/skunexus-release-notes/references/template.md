# Release notes - template

```markdown
## Breaking changes
- <what changed in the contract> - <required action for the consumer>

## <Area, e.g. Custom fields grid & details>
- <new / changed thing in backticks> - <what it gives, one clause>
- <behavior change> - <observable effect>
- <unchanged thing a consumer may worry about> is unchanged - <what still works>

## <Another area, e.g. Extending value type labels>
- <extension point> - <how to use it, one clause>

**Full Changelog**: https://github.com/SkuNexus-Devs/<repo>/compare/<prev-tag>...<new-tag>
```

Drop sections that would be empty - no `## Breaking changes` with "none".

## Example (skunexus-be-custom-fields, CORE-1817)

```markdown
## Custom fields grid & details
- new `value_type_label` field next to `value_type` - human-readable label of the value type (`bool` → Yes/No, `date` → Date, `datetime` → Date and Time, `float` → Number: Decimal, `int` → Number: Integer, `string` → Text)
- custom fields grid can be sorted by `value_type_label` - ordering follows the displayed label instead of the raw code
- `value_type` is unchanged - still selectable, filterable and sortable by code

## Extending value type labels
- `ValueType::labels()` holds the default map - an extending enum can add labels via `parent::labels() + [...]`
- new `ValueTypeLabelsInterface` registry (singleton) - labels can be added with `register()` from a host application's provider, or the binding can be replaced
- custom labels apply to both the field value and the sort order

**Full Changelog**: https://github.com/SkuNexus-Devs/skunexus-be-custom-fields/compare/10.0.0...10.1.0
```

Version: **minor** - new classes, a new interface, new public methods on `ValueType` and a new GraphQL field; no BC break (the only rename concerns a class added in the same range, constructor changes are excluded, no subclasses of the changed classes found).

Left out of this example on purpose: the `composer.lock` refresh and `.gitignore` entry (no effect
on consumers), the internal `ValueTypeLabelField` class name and constructor property promotion
(implementation, not contract), and the reasoning behind sorting via `CASE` in SQL (belongs to the
PR description).
