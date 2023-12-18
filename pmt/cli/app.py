import typer

from pmt.cli import migrate


app = typer.Typer()
app.add_typer(migrate.app, name="migrate")


@app.callback()
def callback():
    pass
