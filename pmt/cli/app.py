import typer

from pmt.cli import upgrade


app = typer.Typer()
app.add_typer(upgrade.app, name="upgrade")


@app.callback()
def callback():
    pass
