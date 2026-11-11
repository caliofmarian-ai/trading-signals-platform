"""Display recorded collection issues without inferring causes from missing prices."""


COLLECTION_ISSUE_LABELS = {
    "EXPIRY_OBSERVATION_MISSING": "Lipsește cotația la expirare",
    "ENTRY_OBSERVATION_MISSING": "Lipsește cotația la intrare",
    "PROVIDER_CHANGED": "Furnizorul de cotații s-a schimbat",
    "ACTIVE_PROVIDER_CHANGED_BEFORE_CHECKPOINT": "Furnizorul de cotații s-a schimbat înainte de expirare",
    "RESTART_MISSED_OBSERVATION": "Colectare întreruptă de repornire",
    "RUNTIME_RESTART_MISSED_CHECKPOINT": "Colectare întreruptă de repornire",
    "LEGACY_PRICE_WITHOUT_RAW_OBSERVATION_TIMESTAMP": "Cotație istorică fără oră verificabilă",
}


def collection_issue_label(reason):
    """A legacy or unrecognized reason is unavailable, never guessed or echoed."""
    if isinstance(reason, str) and reason in COLLECTION_ISSUE_LABELS:
        return COLLECTION_ISSUE_LABELS[reason]
    return "Cauza lipsei datelor este indisponibilă"
