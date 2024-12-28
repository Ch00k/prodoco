from unittest.mock import MagicMock, patch

from prodoco.discovery import DEFAULT_DOCKER_ADDRESS, DEFAULT_SCRAPE_PORT_LABEL, discover

from .docker_api_output import containers


@patch("prodoco.discovery.docker.DockerClient.containers")
def test_discovery(m_containers: MagicMock) -> None:
    m_containers.list.return_value = containers()

    config = discover(
        docker_address=DEFAULT_DOCKER_ADDRESS,
        scrape_port_label=DEFAULT_SCRAPE_PORT_LABEL,
    )

    expected_config = [
        {
            "targets": ["172.17.0.1:5000"],
            "labels": {
                "__meta_dockercompose_container_id": "containerid1",
                "__meta_dockercompose_container_name": "container1",
                "__meta_dockercompose_container_network_mode": "network1",
                "__meta_dockercompose_container_number": "1",
                "__meta_dockercompose_container_service": "service1",
                "__meta_dockercompose_container_project": "project1",
                "__meta_dockercompose_container_project_working_dir": "working_dir1",
            },
        },
        {
            "targets": ["172.17.0.9:5009"],
            "labels": {
                "__meta_dockercompose_container_id": "containerid9",
                "__meta_dockercompose_container_name": "container9",
                "__meta_dockercompose_container_network_mode": "network9",
                "__meta_dockercompose_container_number": "9",
                "__meta_dockercompose_container_service": "service9",
                "__meta_dockercompose_container_project": "project9",
                "__meta_dockercompose_container_project_working_dir": "working_dir9",
            },
        },
    ]

    assert config == expected_config
