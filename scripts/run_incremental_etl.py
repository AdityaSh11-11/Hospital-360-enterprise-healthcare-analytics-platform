from __future__ import annotations

import argparse
import sys

from etl.incremental import (
    discover_batches,
    get_batch,
    get_pending_batches,
    validate_batch_directory,
)

from etl.pipeline import run_etl


# ============================================================
# PRINT HELPERS
# ============================================================

def separator() -> None:

    print(
        "=" * 78
    )


def small_separator() -> None:

    print(
        "-" * 78
    )


def print_batch_list(
    title,
    batches,
) -> None:

    print()
    print(
        title
    )

    small_separator()

    if not batches:

        print(
            "No batches found."
        )

        return

    for batch in batches:

        print(
            f"{batch.batch_id}"
            f" | "
            f"{batch.business_date}"
            f" | "
            f"{batch.path}"
        )


# ============================================================
# PRINT ETL RESULT
# ============================================================

def print_etl_result(
    result: dict,
) -> None:

    print()
    print(
        "ETL RESULT"
    )

    small_separator()

    for key, value in result.items():

        print(
            f"{key:<24}: {value}"
        )


# ============================================================
# PROCESS ONE BATCH
# ============================================================

def process_batch(
    batch,
) -> bool:
    """
    Process one incremental source batch.

    Final warehouse reconciliation is performed inside
    etl.pipeline.run_etl() using source business keys.

    This CLI intentionally does NOT perform before/after
    row-count delta reconciliation because that approach is
    not retry-safe.

    Example:

        A previous partial load may already contain 179 of
        180 admissions.

        A retry inserts only the missing admission.

        Row delta = 1
        Source rows = 180

    That is a successful retry, not a reconciliation failure.

    The pipeline therefore verifies that all 180 source
    admission IDs exist in the warehouse before SUCCESS is
    recorded.
    """

    separator()

    print(
        "HOSPITAL 360 — "
        f"INCREMENTAL ETL — {batch.batch_id}"
    )

    separator()

    print(
        f"Business date : "
        f"{batch.business_date}"
    )

    print(
        f"Source path   : "
        f"{batch.path}"
    )

    # --------------------------------------------------------
    # SOURCE DIRECTORY STRUCTURE CHECK
    # --------------------------------------------------------

    validate_batch_directory(
        batch.path
    )

    # --------------------------------------------------------
    # RUN AUTHORITATIVE ETL PIPELINE
    # --------------------------------------------------------

    result = run_etl(
        source_type="INCREMENTAL",
        source_path=batch.path,
        source_batch_id=batch.batch_id,
        business_date=batch.business_date,
    )

    print_etl_result(
        result
    )

    status = str(
        result.get(
            "status",
            "",
        )
    ).upper()

    # --------------------------------------------------------
    # SUCCESS
    # --------------------------------------------------------

    if status == "SUCCESS":

        print()
        print(
            "[PASS] ETL completed successfully."
        )

        print(
            (
                "[PASS] Source business-key "
                "reconciliation passed inside "
                "the ETL transaction."
            )
        )

        return True

    # --------------------------------------------------------
    # ALREADY LOADED
    # --------------------------------------------------------

    if status == "SKIPPED":

        print()
        print(
            (
                "[SKIP] Batch already has a "
                "successful ETL load."
            )
        )

        return True

    # --------------------------------------------------------
    # UNEXPECTED RESULT
    # --------------------------------------------------------

    print()

    print(
        (
            "[FAIL] ETL returned an unexpected "
            f"status: {status or 'UNKNOWN'}"
        )
    )

    return False


# ============================================================
# CLI
# ============================================================

def build_parser():

    parser = argparse.ArgumentParser(
        description=(
            "Hospital 360 incremental "
            "warehouse ETL orchestrator."
        )
    )

    mode = (
        parser.add_mutually_exclusive_group(
            required=True
        )
    )

    mode.add_argument(
        "--all-pending",
        action="store_true",
        help=(
            "Process all incremental batches "
            "that have not completed successfully."
        ),
    )

    mode.add_argument(
        "--batch",
        type=str,
        help=(
            "Process one batch, for example "
            "BATCH-20260925-002."
        ),
    )

    mode.add_argument(
        "--list",
        action="store_true",
        help=(
            "List discovered and pending "
            "incremental batches."
        ),
    )

    return parser


# ============================================================
# LIST MODE
# ============================================================

def run_list_mode() -> None:

    discovered = (
        discover_batches()
    )

    pending = (
        get_pending_batches()
    )

    separator()

    print(
        "HOSPITAL 360 — "
        "INCREMENTAL BATCH DISCOVERY"
    )

    separator()

    print_batch_list(
        "DISCOVERED BATCHES",
        discovered,
    )

    print_batch_list(
        "PENDING BATCHES",
        pending,
    )

    separator()


# ============================================================
# SINGLE BATCH MODE
# ============================================================

def run_single_batch_mode(
    batch_id: str,
) -> None:

    batch = get_batch(
        batch_id
    )

    try:

        success = process_batch(
            batch
        )

    except Exception as exc:

        print()
        separator()

        print(
            "[FAIL] Incremental ETL failed."
        )

        print(
            f"Batch  : {batch.batch_id}"
        )

        print(
            f"Reason : {exc}"
        )

        separator()

        raise

    if not success:

        sys.exit(1)


# ============================================================
# ALL PENDING MODE
# ============================================================

def run_all_pending_mode() -> None:

    pending = (
        get_pending_batches()
    )

    separator()

    print(
        "HOSPITAL 360 — "
        "ALL PENDING INCREMENTAL ETL"
    )

    separator()

    if not pending:

        print()
        print(
            "No pending incremental batches."
        )

        print()

        separator()

        return

    print()

    print(
        f"Pending batches : "
        f"{len(pending)}"
    )

    for batch in pending:

        print(
            f"  - {batch.batch_id}"
        )

    print()

    successful = 0
    skipped = 0

    for batch in pending:

        try:

            # ------------------------------------------------
            # Validate source structure before processing.
            # ------------------------------------------------

            validate_batch_directory(
                batch.path
            )

            # ------------------------------------------------
            # Run ETL.
            # ------------------------------------------------

            separator()

            print(
                "HOSPITAL 360 — "
                f"INCREMENTAL ETL — "
                f"{batch.batch_id}"
            )

            separator()

            print(
                f"Business date : "
                f"{batch.business_date}"
            )

            print(
                f"Source path   : "
                f"{batch.path}"
            )

            result = run_etl(
                source_type="INCREMENTAL",
                source_path=batch.path,
                source_batch_id=batch.batch_id,
                business_date=batch.business_date,
            )

            print_etl_result(
                result
            )

            status = str(
                result.get(
                    "status",
                    "",
                )
            ).upper()

            if status == "SUCCESS":

                successful += 1

                print()
                print(
                    "[PASS] ETL completed successfully."
                )

                print(
                    (
                        "[PASS] Source business-key "
                        "reconciliation passed inside "
                        "the ETL transaction."
                    )
                )

            elif status == "SKIPPED":

                skipped += 1

                print()
                print(
                    (
                        "[SKIP] Batch already has "
                        "a successful ETL load."
                    )
                )

            else:

                raise RuntimeError(
                    (
                        "Unexpected ETL status "
                        f"'{status or 'UNKNOWN'}' "
                        f"for {batch.batch_id}."
                    )
                )

        except Exception as exc:

            print()
            separator()

            print(
                "[FAIL] Incremental ETL stopped."
            )

            print(
                f"Batch  : {batch.batch_id}"
            )

            print(
                f"Reason : {exc}"
            )

            print(
                (
                    "Later pending batches were "
                    "not processed."
                )
            )

            separator()

            raise

    print()

    separator()

    print(
        "INCREMENTAL ETL COMPLETE"
    )

    print(
        f"Successful batches : "
        f"{successful}"
    )

    print(
        f"Skipped batches    : "
        f"{skipped}"
    )

    print(
        f"Total processed    : "
        f"{successful + skipped}"
    )

    separator()


# ============================================================
# MAIN
# ============================================================

def main() -> None:

    parser = build_parser()

    args = parser.parse_args()

    # ========================================================
    # LIST
    # ========================================================

    if args.list:

        run_list_mode()

        return

    # ========================================================
    # SPECIFIC BATCH
    # ========================================================

    if args.batch:

        run_single_batch_mode(
            args.batch
        )

        return

    # ========================================================
    # ALL PENDING
    # ========================================================

    if args.all_pending:

        run_all_pending_mode()

        return

    # Defensive fallback.
    parser.error(
        "No execution mode selected."
    )


if __name__ == "__main__":

    main()