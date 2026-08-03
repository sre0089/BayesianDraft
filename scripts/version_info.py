from bayesiandraft.release import build_info_from_env


def main() -> None:
    print(build_info_from_env().model_dump_json())


if __name__ == "__main__":
    main()
