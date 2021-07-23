import click

from .southeast_pa_funding_options import southeast_pa_funding_options


@click.group()
def main():
    "The command 'survey' is used to summzarize Google Forms survey data"
    pass


_all_commands = [southeast_pa_funding_options]

for cmd in _all_commands:
    main.add_command(cmd)
