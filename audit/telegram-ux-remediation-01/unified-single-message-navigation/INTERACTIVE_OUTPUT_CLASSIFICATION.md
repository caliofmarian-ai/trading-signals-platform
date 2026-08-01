# Interactive Output Classification

## Interactive application pages (single-message canonical path)
- Public pages: start/help/status/home/admin pointer
- Admin pages/panels and nested panel pages
- Access-denied pages for navigation/commands
- Unknown-action/unknown-command pages
- Rate-limit pages for interactive routes

## Callback toast / ephemeral feedback
- Outcome callback acknowledgements in `runtime/telegram_updates._answer_callback_query` for vote callbacks

## File/document delivery (permitted separate messages)
- `sendDocument` file export/download paths (`FILE_DL`, `LOG`, `AUDIT`, docs/files/report downloads)

## Signal publication (permitted separate messages)
- Distribution router signal/channel publication messages

## Operational alert / observability proof (permitted separate messages)
- Observability notifications and startup/operational alerts

## Audit/proof notifications (permitted separate messages)
- Runtime/observability proof events and related outbound telemetry notifications
