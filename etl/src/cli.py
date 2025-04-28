# Entry point for the ETL CLI application
import typer

# import subprocess # Temporarily commented out
# import os # Temporarily commented out
from typing_extensions import Annotated

app = typer.Typer(help="NIP ETL command-line interface.")


@app.command()
def run(
    extractor: Annotated[
        str, typer.Option(help="Extractor to run (e.g., tap-chartmetric).")
    ],
    loader: Annotated[
        str, typer.Option(help="Loader to use (e.g., target-jsonl, target-bigquery).")
    ],
):
    """*MOCK RUN* Displays the Meltano ETL command that would be executed."""
    typer.echo(f"*MOCK RUN* Planning pipeline: {extractor} -> {loader}")

    cmd = ["meltano", "run", extractor, loader]

    typer.echo(f"Would execute command: {' '.join(cmd)}")
    typer.secho(
        "Actual execution is disabled pending Meltano environment troubleshooting.",
        fg=typer.colors.YELLOW,
    )

    # Temporarily disable subprocess execution
    # meltano_executable = "meltano"
    # cmd[0] = meltano_executable
    # try:
    #     etl_dir = os.path.dirname(os.path.dirname(__file__))
    #     result = subprocess.run(cmd, cwd=etl_dir, check=True, capture_output=True, text=True)
    #     typer.echo("Meltano output:")
    #     typer.echo(result.stdout)
    #     typer.secho("ETL run completed successfully.", fg=typer.colors.GREEN)
    # except subprocess.CalledProcessError as e:
    #     typer.secho(f"ETL run failed!", fg=typer.colors.RED)
    #     typer.echo(f"Return code: {e.returncode}")
    #     typer.echo("Stderr:")
    #     typer.echo(e.stderr)
    # except FileNotFoundError:
    #     typer.secho(f"Error: '{meltano_executable}' command not found.", fg=typer.colors.RED)
    #     typer.echo("Ensure meltano is installed and in your PATH or run via poetry.")


@app.command()
def some_other_command():
    """Placeholder for another ETL-related command."""
    typer.echo("Running some other command...")


if __name__ == "__main__":
    app()
