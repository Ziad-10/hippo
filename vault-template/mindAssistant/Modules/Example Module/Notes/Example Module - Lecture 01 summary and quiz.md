# Example Module - Lecture 01 summary and quiz

Date: 2026-10-20 · Source: `Materials/Lectures/01-searching.pdf` · Module: [[Example Module]]

*Demo note showing the kind of result the assistant saves after a study session.*

## Summary

- **Linear search** checks every element: O(n), works on unsorted data.
- **Binary search** halves a sorted range each step: O(log n). The invariant: if the target exists, it lies in `[lo, hi]`.
- Off-by-one errors come from mixing half-open `[lo, hi)` and closed `[lo, hi]` ranges.

## Quiz (one question at a time)

| # | Question | Result | Feedback |
|---|---|---|---|
| 1 | Worst-case comparisons for binary search on 1,000 items? | ✅ | ~10, since 2¹⁰ ≈ 1,000. |
| 2 | Why must the input be sorted? | ✅ | Discarding half the range relies on order. |
| 3 | Write the loop condition for a closed range. | ❌ → ✅ | First answer used `lo < hi`, which skips the last element; corrected to `lo <= hi`. |

## Weak topics

- Loop invariants and range conventions → added to [[Example Module]].

## Next step

- Exercise sheet 1, task 2, before the next lecture.
