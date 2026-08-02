from argparse import ArgumentParser
from pathlib import Path

from bayesiandraft.data import load_ingestion_manifest, verify_ingestion_manifest


def main() -> None:
    parser = ArgumentParser(description="Verify a BayesianDraft ingestion manifest.")
    parser.add_argument(
        "manifest",
        help="Path to an ingestion manifest JSON file.",
    )
    parser.add_argument(
        "--root",
        default=".",
        help="Repository or data root used to resolve manifest paths.",
    )
    args = parser.parse_args()

    manifest = load_ingestion_manifest(args.manifest)
    verify_ingestion_manifest(manifest, root=Path(args.root))
    print(f"verified {manifest.snapshot_id}")


if __name__ == "__main__":
    main()
