import tyro

from src.config import Config


def main():
    args = tyro.cli(Config)
    print(args)


if __name__ == "__main__":
    main()
