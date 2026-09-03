# Relations

Model relations generically, then let the platform adapter map them to the tracker's native links. Show the relation graph in the plan preview so the user approves the structure, not just the items.

## Relation types

| Relation | Meaning |
|---|---|
| parent / child | Containment: an epic contains stories, a story contains sub-tasks. |
| needs | A prerequisite. This item cannot start until the other is done. |
| depends-on | This item requires the other, without the hard "not before" of needs. |
| blocks / blocked-by | This item stops another from progressing, or is stopped by it. |
| relates-to | A soft link worth surfacing, no ordering implied. |
| duplicates | Same work as another item. Usually resolve before creating. |

## In the plan preview

Show the graph plainly, for example:

```
Epic: Checkout redesign
├─ Story A: Cart summary
├─ Story B: Payment step         needs -> Story A
├─ Story C: Order confirmation   blocked-by -> Story B
└─ Task D: Feature flag           relates-to -> Epic
```

## Mapping

Each platform adapter states how it expresses these:

- parent/child through native sub-issues, an Epic Link, or checklists.
- needs, depends-on, and blocks through native issue links where they exist, or a stated convention where they do not.

Do not invent a link type the tracker cannot express. When a relation has no native equivalent, record it in the item body and say so.
