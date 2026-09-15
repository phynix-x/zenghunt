import logging

from .connectors import configured_connectors
from .supabase import SupabaseWriter

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger("zenghunt")


def main():
    connectors = configured_connectors()
    if not connectors:
        log.warning("No store feeds configured. Nothing was inserted; this is intentional until approved data sources are configured.")
        return

    writer = SupabaseWriter()
    total = 0
    for connector in connectors:
        count = 0
        try:
            for offer in connector.fetch():
                writer.record(offer)
                count += 1
                total += 1
            log.info("%s: collected %d real offers", connector.name, count)
        except Exception as exc:
            log.exception("%s connector failed: %s", connector.name, exc)
    log.info("Collection finished: %d offers", total)


if __name__ == "__main__":
    main()
