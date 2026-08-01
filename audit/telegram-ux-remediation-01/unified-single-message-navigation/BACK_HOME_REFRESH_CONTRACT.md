# Back / Home / Refresh Contract

## Parent integrity
- Admin panel "Back" buttons route to valid parent callbacks (`HOME`, `FILES_HOME`, `STRATEGY`)
- Home routes to admin root/home panel depending on context
- Refresh routes point to same panel action and are idempotent

## Delivery integrity
- Back/Home/Refresh actions now use canonical interactive delivery path
- All update one interactive message (edit preferred origin, else active tracked)
- No dead-end page paths identified in routed admin/app panels
