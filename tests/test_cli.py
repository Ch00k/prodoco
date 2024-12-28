from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from prodoco.discovery import cli

from .docker_api_output import containers

expected_output = """
- targets:
  - 172.17.0.1:5000
  labels:
    __meta_dockercompose_container_id: containerid1
    __meta_dockercompose_container_name: container1
    __meta_dockercompose_container_network_mode: network1
    __meta_dockercompose_container_number: '1'
    __meta_dockercompose_container_project: project1
    __meta_dockercompose_container_project_working_dir: working_dir1
    __meta_dockercompose_container_service: service1
- targets:
  - 172.17.0.9:5009
  labels:
    __meta_dockercompose_container_id: containerid9
    __meta_dockercompose_container_name: container9
    __meta_dockercompose_container_network_mode: network9
    __meta_dockercompose_container_number: '9'
    __meta_dockercompose_container_project: project9
    __meta_dockercompose_container_project_working_dir: working_dir9
    __meta_dockercompose_container_service: service9
"""


@patch("prodoco.discovery.docker.DockerClient.containers")
def test_no_options(m_containers: MagicMock) -> None:
    m_containers.list.return_value = containers()
    runner = CliRunner(mix_stderr=False)
    result = runner.invoke(cli)

    assert result.exit_code == 0
    assert result.stdout == expected_output


@patch("prodoco.discovery.docker.DockerClient.containers")
def test_output_to_file(m_containers: MagicMock) -> None:
    m_containers.list.return_value = containers()
    runner = CliRunner(mix_stderr=False)

    with runner.isolated_filesystem():
        result = runner.invoke(cli, ["--output-file", "output.yml"])

        with open("output.yml") as f:
            assert f.read() == expected_output.lstrip()

    assert result.exit_code == 0
