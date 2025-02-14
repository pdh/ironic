import click
from ironic.core import SimpleInfrastructure
from ironic.exceptions import DeploymentError
import json

@click.group()
def cli():
    """Simple Infrastructure Deployment Tool"""
    pass

@cli.command()
@click.option('--config', '-c', default='config.yaml', help='Path to configuration file')
def deploy(config):
    """Deploy services based on configuration"""
    try:
        infra = SimpleInfrastructure(config)
        report = infra.deploy()
        click.echo("Deployment completed!")
        click.echo("\nDeployment Report:")
        click.echo(json.dumps(report, indent=2))
    except DeploymentError as e:
        click.echo(f"Deployment failed: {str(e)}", err=True)
        exit(1)