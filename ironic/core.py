import paramiko
from paramiko import SSHClient
from scp import SCPClient
import logging
from .exceptions import DeploymentError
from .models import DeploymentTracker, DeploymentStep

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimpleInfrastructure:
    def __init__(self, config_path: str):
        self.config = self._load_config(config_path)
        self.ssh_client = SSHClient()
        self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.deployment_tracker = DeploymentTracker()

    def _track_step(self, name: str, service: str, host: str) -> DeploymentStep:
        step = DeploymentStep(name, service, host)
        self.deployment_tracker.add_step(step)
        return step

    def deploy_image(self, image_name: str, host: dict):
        step = self._track_step("deploy_image", image_name, host['name'])
        step.start()
        logger.info(f"Deploying image {image_name} to {host['name']}")
        
        try:
            self.ssh_client.connect(host['ip'], username=host['user'])
            stdin, stdout, stderr = self.ssh_client.exec_command(
                f"docker save {image_name} | docker load"
            )
            exit_status = stdout.channel.recv_exit_status()
            
            if exit_status != 0:
                error_msg = stderr.read().decode()
                step.fail(error_msg)
                raise DeploymentError(f"Failed to deploy image: {error_msg}")
                
            step.complete()
            logger.info(f"Successfully deployed image {image_name}")
            
        except Exception as e:
            step.fail(str(e))
            raise DeploymentError(f"Failed to deploy image: {str(e)}")

    def copy_files(self, files: list, host: dict):
        step = self._track_step("copy_files", "files", host['name'])
        step.start()
        logger.info(f"Copying files to {host['name']}")
        
        try:
            self.ssh_client.connect(host['ip'], username=host['user'])
            with SCPClient(self.ssh_client.get_transport()) as scp:
                for file in files:
                    scp.put(file['src'], file['dest'])
            step.complete()
            logger.info("Successfully copied files")
            
        except Exception as e:
            step.fail(str(e))
            raise DeploymentError(f"Failed to copy files: {str(e)}")

    def deploy_service(self, service: dict, host: dict):
        step = self._track_step("deploy_service", service['name'], host['name'])
        step.start()
        logger.info(f"Deploying service {service['name']} to {host['name']}")
        
        try:
            self.ssh_client.connect(host['ip'], username=host['user'])
            
            if 'compose_file' in service:
                self.copy_files([{'src': service['compose_file'], 'dest': '/tmp/docker-compose.yml'}], host)
            
            if 'files' in service:
                self.copy_files(service['files'], host)
                
            if 'image' in service:
                self.deploy_image(service['image'], host)
                
            stdin, stdout, stderr = self.ssh_client.exec_command(
                'cd /tmp && docker-compose up -d'
            )
            
            if stdout.channel.recv_exit_status() != 0:
                error_msg = stderr.read().decode()
                step.fail(error_msg)
                raise DeploymentError(f"Failed to start service: {error_msg}")
                
            step.complete()
            logger.info(f"Successfully deployed service {service['name']}")
            
        except Exception as e:
            step.fail(str(e))
            raise DeploymentError(f"Failed to deploy service: {str(e)}")

    def deploy(self):
        """Main deployment method"""
        try:
            for host in self.config['infrastructure']['hosts']:
                logger.info(f"Deploying to host: {host['name']}")
                
                for service in self.config['services']:
                    logger.info(f"Deploying service: {service['name']}")
                    self.deploy_service(service, host)
                    
            self.deployment_tracker.complete()
            return self.deployment_tracker.generate_report()
            
        except Exception as e:
            self.deployment_tracker.complete()
            logger.error(f"Deployment failed: {str(e)}")
            raise