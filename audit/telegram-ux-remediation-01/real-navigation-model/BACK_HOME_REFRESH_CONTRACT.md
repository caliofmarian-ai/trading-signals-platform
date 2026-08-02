# Back / Home / Refresh Contract

## APP
- Entering a new APP page records the current APP page once, unless the destination is the same logical page.
- Refresh re-renders the current page and does not grow history.
- Back pops exactly one validated parent and does not push the page being left.
- Home clears APP history for the current `(chat_id, user_id, thread_id)` session.
- `/start` clears APP history and starts a new callback generation.

## Admin
- Back uses canonical callback destinations, not an implicit stack.
- Refresh always re-renders the same logical admin surface.
- Cancel buttons return to the immediate pre-confirmation parent.
- File/document downloads are sent separately and leave the listing anchor in place when the download succeeds.
