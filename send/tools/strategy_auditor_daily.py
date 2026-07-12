import sys
import traceback

from strategy_auditor_lib import (
    load_settings,
    load_all_events,
    build_report,
    write_reports,
)


def run_auditor():

    try:

        settings = load_settings()

        events = load_all_events(settings)

        report = build_report(events, settings)

        write_reports(report, settings)

        print("Strategy auditor completed successfully.")
        print("Report date:", report["date"])
        print("Total decisions:", report["decisions"])

    except Exception as e:

        print("Strategy auditor failed.")
        print(str(e))
        traceback.print_exc()


if __name__ == "__main__":
    run_auditor()