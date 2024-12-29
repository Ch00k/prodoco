import logging
import logging.config
import time
from typing import IO, Any, Mapping

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
    # https://stackoverflow.com/a/65692753
    def represent_none(self: Any, _: Any) -> Any:
        return self.represent_scalar("tag:yaml.org,2002:null", "null")

    yaml = YAML()
    yaml.representer.add_representer(type(None), represent_none)
    yaml.dump(data, fp)


CONTEXT_SETTINGS = {"max_content_width": 110}

DEFAULT_DOCKER_ADDRESS = "unix:///var/run/docker.sock"
DEFAULT_SCRAPE_PORT_LABEL = "prometheus.scrape-port"


@click.command(context_settings=CONTEXT_SETTINGS)
@click.option(
    "-a",
    "--docker-address",
    type=str,
    default=DEFAULT_DOCKER_ADDRESS,
    help=(
        "Docker daemon address. Can be a UNIX socket, a TCP, or an HTTP(S) address. "
        f"Default: {DEFAULT_DOCKER_ADDRESS}"
    ),
)
@click.option(
    "-p",
    "--scrape-port-label",
    type=str,
    default=DEFAULT_SCRAPE_PORT_LABEL,
    help=f"Container label that enables scraping and contains the port to scrape. Default: {DEFAULT_SCRAPE_PORT_LABEL}",
)
@click.option(
    "-o",
    "--output-file",
    type=click.Path(),
    help="File to write the discovery configuration to. Default: unset (configuration is written to STDOUT)",
)
@click.option(
    "-i",
    "--interval",
    type=click.IntRange(1),
    help="Run discovery every INTERVAL seconds. Default: unset (run discovery only once)",
)
def cli(docker_address: str, scrape_port_label: str, output_file: str | None, interval: int | None) -> None:
    """Generate a file in YAML format to be used for service discovery in Prometheus (aka file_sd_configs)"""
    if interval:
        logger.info(f"Running discovery every {interval} seconds")
        scheduler = BlockingScheduler()
        scheduler.add_job(
            func=job,
            trigger="interval",
            args=[docker_address, scrape_port_label, output_file],
            seconds=interval,
        )
        scheduler.start()
    else:
        config = discover(docker_address, scrape_port_label)
        write_config(config, output_file)


def discover(docker_address: str, scrape_port_label: str) -> list[dict[str, Any]]:
    logger.info(f"Discovering containers with label '{scrape_port_label}'")

    client = docker.DockerClient(base_url=docker_address)
    containers = client.containers.list(filters={"label": scrape_port_label})

    logger.info(f"Found {len(containers)} containers with label '{scrape_port_label}'")

    config = []

    for container in containers:
        logger.info(f"Processing container '{container.name}'")

        scrape_port = container.labels.get(scrape_port_label)
        if scrape_port:
            logger.info(f"Container '{container.name}' has value '{scrape_port}' for '{scrape_port_label}' label")
        else:
            logger.warning(f"Container '{container.name}' has no value for '{scrape_port_label}' label. Skipping")
            continue

        try:
            scrape_port = int(scrape_port)
        except Exception:
            logger.error(
                f"Container '{container.name}' has an invalid value '{scrape_port}' for '{scrape_port_label}' label"
            )
            continue

        networks = container.attrs.get("NetworkSettings", {}).get("Networks")
        if not networks or not isinstance(networks, Mapping):
            logger.warning(f"Container '{container.name}' has no networks. Skipping")
            continue

        networks = list(networks.values())

        # TODO: Handle multiple networks?
        ip_address = networks[0]["IPAddress"]
        target = f"{ip_address}:{scrape_port}"

        logger.info(f"Container '{container.name}' target: '{target}'")

        # docker_sd_config labels (https://prometheus.io/docs/prometheus/latest/configuration/configuration/#docker_sd_config)
        # __meta_dockercompose_container_id: the id of the container
        # __meta_dockercompose_container_name: the name of the container
        # __meta_dockercompose_container_network_mode: the network mode of the container
        # __meta_dockercompose_container_label_<labelname>: each label of the container, with any unsupported characters converted to an underscore
        # __meta_dockercompose_network_id: the ID of the network
        # __meta_dockercompose_network_name: the name of the network
        # __meta_dockercompose_network_ingress: whether the network is ingress
        # __meta_dockercompose_network_internal: whether the network is internal
        # __meta_dockercompose_network_label_<labelname>: each label of the network, with any unsupported characters converted to an underscore
        # __meta_dockercompose_network_scope: the scope of the network
        # __meta_dockercompose_network_ip: the IP of the container in this network
        # __meta_dockercompose_port_private: the port on the container
        # __meta_dockercompose_port_public: the external port if a port-mapping exists
        # __meta_dockercompose_port_public_ip: the public IP if a port-mapping exists

        # Docker Compose labels
        # "com.docker.compose.config-hash": "b9b86df4bdcd1a7f5b22006dec33d2b606f60ebd7e95abe04436bad8bc06c979",
        # "com.docker.compose.container-number": "1",
        # "com.docker.compose.depends_on": "",
        # "com.docker.compose.image": "sha256:82cda799cc0246345d5f4c0c6d0c2d39a46ad4a0f4e9ab4f16a3e2d52528cfed",
        # "com.docker.compose.oneoff": "False",
        # "com.docker.compose.project": "mottle",
        # "com.docker.compose.project.config_files": "/home/ay/projects/live/mottle/docker-compose.yml",
        # "com.docker.compose.project.working_dir": "/home/ay/projects/live/mottle",
        # "com.docker.compose.service": "grafana",
        # "com.docker.compose.version": "2.32.1",
        # "maintainer": "Grafana Labs <hello@grafana.com>",

        # TODO: Add all `docker_sd_config` labels
        labels = {
            "__meta_dockercompose_container_id": container.id,
            "__meta_dockercompose_container_name": container.name,
            "__meta_dockercompose_container_network_mode": container.attrs["HostConfig"]["NetworkMode"],
            "__meta_dockercompose_container_number": container.labels.get("com.docker.compose.container-number"),
            "__meta_dockercompose_container_project": container.labels.get("com.docker.compose.project"),
            "__meta_dockercompose_container_project_working_dir": container.labels.get(
                "com.docker.compose.project.working_dir"
            ),
            "__meta_dockercompose_container_service": container.labels.get("com.docker.compose.service"),
        }

        config.append({"targets": [target], "labels": labels})

    return config


def write_config(config: list, output_file: str | None) -> None:
    if output_file is None:
        click.echo()
        write_as_yaml(config, click.get_text_stream("stdout"))
    else:
        with open(output_file, "w") as f:
            write_as_yaml(config, f)


def job(docker_address: str, metrics_port_label: str, output_file: str | None) -> None:
    config = discover(docker_address, metrics_port_label)
    write_config(config, output_file)
