from argparse import ArgumentParser

from bayesiandraft_api.contracts import write_openapi_schema
from bayesiandraft_api.main import create_app


def main() -> None:
    parser = ArgumentParser(description="Export BayesianDraft OpenAPI schema.")
    parser.add_argument("--out", required=True, help="Output JSON path.")
    args = parser.parse_args()

    write_openapi_schema(create_app(), args.out)


if __name__ == "__main__":
    main()
