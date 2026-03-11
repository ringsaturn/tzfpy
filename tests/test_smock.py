from tzfpy import get_tz


def run() -> None:
    name = get_tz(135.0, 35.0)
    print(name)


def test_smock() -> None:
    run()


if __name__ == "__main__":
    run()
