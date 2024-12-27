import logging
import logging.config
import time
from typing import IO

import click
import docker
from apscheduler.schedulers.blocking import BlockingScheduler
from ruamel.yaml import YAML

from .logger import LOGGING


class UTCFormatter(logging.Formatter):
    converter = time.gmtime


logging.config.dictConfig(LOGGING)
logger = logging.getLogger(__name__)


def write_as_yaml(data: dict | list, fp: IO) -> None:
    yaml = YAML()
    yaml.dump(data, fp)


@click.command()
@click.option("-a", "--docker-address", type=str, default="unix://var/run/docker.sock")
@click.option("-s", "--scrape-label", type=str, default="prometheus-scrape")
@click.option("-p", "--metrics-port-label", type=str, default="prometheus-metrics-port")
@click.option("-o", "--output-file", type=click.Path(), default="-")
@click.option("-e", "--run-every-seconds", type=int, default=0)
def cli(
    docker_address: str, scrape_label: str, metrics_port_label: str, output_file: str, run_every_seconds: int
) -> None:
    if run_every_seconds > 0:
        logger.info(f"Running discovery every {run_every_seconds} seconds")
        scheduler = BlockingScheduler()
        scheduler.add_job(
            func=discover,
            trigger="interval",
            args=[docker_address, scrape_label, metrics_port_label, output_file],
            seconds=run_every_seconds,
        )
        scheduler.start()
    else:
        discover(docker_address, scrape_label, metrics_port_label, output_file)


def discover(docker_address: str, scrape_label: str, metrics_port_label: str, output_file: str) -> None:
    logger.info(f"Discovering containers with label '{scrape_label}'")

    client = docker.DockerClient(base_url=docker_address)
    containers = client.containers.list(filters={"label": scrape_label})

    logger.info(f"Found {len(containers)} containers with label '{scrape_label}'")

    config = []

    for container in containers:
        logger.info(f"Processing container '{container.name}'")

        ports = container.ports
        logger.info(f"Container '{container.name}' has {len(ports)} exposed ports")

        if len(ports) < 1:
            logger.warning(f"Container '{container.name}' has no exposed ports. Skipping")
            continue
        elif len(ports) > 1:
            logger.warning(
                f"Container '{container.name}' has more than one exposed port. "
                f"Checking value of label '{metrics_port_label}'"
            )

            metrics_port = container.labels.get(metrics_port_label)

            if not metrics_port:
                logger.warning(f"Container '{container.name}' has no '{metrics_port_label}' label. Skipping")
                continue

            logger.info(f"Container '{container.name}' has '{metrics_port_label}' label with value '{metrics_port}'")

            port, port_config = None, None

            for exposed_port, host_port in ports.items():
                if host_port[0]["HostPort"] == metrics_port:
                    port = exposed_port
                    port_config = host_port[0]
                    break
            else:
                logger.warning(
                    f"Container '{container.name}' has no exposed port matching '{metrics_port}' value. Skipping"
                )
                continue
        else:
            port = list(ports.keys())[0]
            port_config = ports[port][0]

        logger.info(f"Container '{container.name}' exposed metrics port configuration: {port_config}")

        if not port.endswith("/tcp"):
            logger.warning(f"Container '{container.name}' exposed port configuration is incorrect. Skipping")
            continue

        port_config = port_config
        host_ip = port_config["HostIp"]
        host_port = port_config["HostPort"]

        if host_ip not in ("0.0.0.0", "127.0.0.1"):
            logger.warning(f"Container '{container.name}' exposed port is not bound to 127.0.0.1. Skipping")
            continue

        target = f"{host_ip}:{host_port}"

        docker_compose_project = container.labels.get("com.docker.compose.project")
        docker_compose_service = container.labels.get("com.docker.compose.service")
        instance = container.name
        container_number = container.labels.get("com.docker.compose.container-number")
        container_image = container.image.tags[0]

        config.append(
            {
                "targets": [target],
                "labels": {
                    "job": docker_compose_project,
                    "service": docker_compose_service,
                    "instance": instance,
                    "container_number": container_number,
                    "contaner_image": container_image,
                },
            }
        )

    if output_file == "-":
        click.echo()
        write_as_yaml(config, click.get_text_stream("stdout"))
    else:
        with open(output_file, "w") as f:
            write_as_yaml(config, f)
