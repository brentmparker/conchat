import argparse
from os import chdir, path
import sys

from server import run_server
from client import run_client


def main(args: argparse.Namespace):
    host = args.host if args.host else "127.0.0.1"
    port = args.port if args.port else 5001
    test = args.test
    protocol = args.protocol
    server = args.server
    if server:
        print("Start server")
        run_server(host=host, port=port)

    run_client(host=host, port=port, test=test, protocol_type=protocol)


if __name__ == "__main__":
    chdir(path.dirname(path.abspath(__file__)))
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--server", "-s", default=False, action="store_true", help="Start chat server"
    )
    parser.add_argument(
        "--test",
        "-t",
        default=False,
        action="store_true",
        help="Start chat client in testing mode",
    )
    parser.add_argument("--host", type=str, help="Specify hostname of client/server")
    parser.add_argument("--port", "-p", type=int, help="Specify port for server/client")
    parser.add_argument("--protocol", default="basic")
    arguments = parser.parse_args(sys.argv[1:])
    main(args=arguments)
