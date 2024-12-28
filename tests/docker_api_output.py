from unittest.mock import MagicMock


def containers() -> list[MagicMock]:
    # Include: container with `prometheus.scrape-port` label
    container_1 = MagicMock(
        id="containerid1",
        attrs={
            "HostConfig": {"NetworkMode": "network1"},
            "NetworkSettings": {"Networks": {"network1": {"IPAddress": "172.17.0.1"}}},
        },
        labels={
            "prometheus.scrape-port": "5000",
            "com.docker.compose.project": "project1",
            "com.docker.compose.service": "service1",
            "com.docker.compose.container-number": "1",
            "com.docker.compose.project.working_dir": "working_dir1",
        },
    )
    container_1.name = "container1"

    # Exclude: container without `prometheus.scrape-port` label
    container_2 = MagicMock(
        id="containerid2",
        attrs={
            "HostConfig": {"NetworkMode": "network2"},
            "NetworkSettings": {"Networks": {"network1": {"IPAddress": "172.17.0.2"}}},
        },
        labels={
            "com.docker.compose.project": "project2",
            "com.docker.compose.service": "service2",
            "com.docker.compose.container-number": "2",
            "com.docker.compose.project.working_dir": "working_dir2",
        },
    )
    container_2.name = "container2"

    # Exclude: container with `prometheus.scrape-port` label, but without a port value
    container_3 = MagicMock(
        id="containerid3",
        attrs={
            "HostConfig": {"NetworkMode": "network3"},
            "NetworkSettings": {"Networks": {"network1": {"IPAddress": "172.17.0.3"}}},
        },
        labels={
            "prometheus.scrape-port": "",
            "com.docker.compose.project": "project3",
            "com.docker.compose.service": "service3",
            "com.docker.compose.container-number": "3",
            "com.docker.compose.project.working_dir": "working_dir3",
        },
    )
    container_3.name = "container3"

    # Exclude: container with `prometheus.scrape-port` label, but with an invalid port value
    container_4 = MagicMock(
        id="containerid4",
        attrs={
            "HostConfig": {"NetworkMode": "network4"},
            "NetworkSettings": {"Networks": {"network1": {"IPAddress": "172.17.0.4"}}},
        },
        labels={
            "prometheus.scrape-port": "foo",
            "com.docker.compose.project": "project4",
            "com.docker.compose.service": "service4",
            "com.docker.compose.container-number": "4",
            "com.docker.compose.project.working_dir": "working_dir4",
        },
    )
    container_4.name = "container4"

    # Exclude: no `NetworkSettings` attribute
    container_5 = MagicMock(
        id="containerid5",
        attrs={
            "HostConfig": {"NetworkMode": "network5"},
        },
        labels={
            "prometheus.scrape-port": "5005",
            "com.docker.compose.project": "project5",
            "com.docker.compose.service": "service5",
            "com.docker.compose.container-number": "5",
            "com.docker.compose.project.working_dir": "working_dir5",
        },
    )
    container_5.name = "container5"

    # Exclude: no `Networks` attribute
    container_6 = MagicMock(
        id="containerid6",
        attrs={
            "HostConfig": {"NetworkMode": "network6"},
            "NetworkSettings": {},
        },
        labels={
            "prometheus.scrape-port": "5006",
            "com.docker.compose.project": "project6",
            "com.docker.compose.service": "service6",
            "com.docker.compose.container-number": "6",
            "com.docker.compose.project.working_dir": "working_dir6",
        },
    )
    container_6.name = "container6"

    # Exclude: `Networks` attribute is empty
    container_7 = MagicMock(
        id="containerid7",
        attrs={
            "HostConfig": {"NetworkMode": "network7"},
            "NetworkSettings": {"Networks": {}},
        },
        labels={
            "prometheus.scrape-port": "5007",
            "com.docker.compose.project": "project7",
            "com.docker.compose.service": "service7",
            "com.docker.compose.container-number": "7",
            "com.docker.compose.project.working_dir": "working_dir7",
        },
    )
    container_7.name = "container7"

    # Exclude: `Networks` attribute is not a mapping
    container_8 = MagicMock(
        id="containerid8",
        attrs={
            "HostConfig": {"NetworkMode": "network8"},
            "NetworkSettings": {"Networks": "foo"},
        },
        labels={
            "prometheus.scrape-port": "5008",
            "com.docker.compose.project": "project8",
            "com.docker.compose.service": "service8",
            "com.docker.compose.container-number": "8",
            "com.docker.compose.project.working_dir": "working_dir8",
        },
    )
    container_8.name = "container8"

    # Include: container with `prometheus.scrape-port` label
    container_9 = MagicMock(
        id="containerid9",
        attrs={
            "HostConfig": {"NetworkMode": "network9"},
            "NetworkSettings": {"Networks": {"network9": {"IPAddress": "172.17.0.9"}}},
        },
        labels={
            "prometheus.scrape-port": "5009",
            "com.docker.compose.project": "project9",
            "com.docker.compose.service": "service9",
            "com.docker.compose.container-number": "9",
            "com.docker.compose.project.working_dir": "working_dir9",
        },
    )
    container_9.name = "container9"

    return [
        container_1,
        container_2,
        container_3,
        container_4,
        container_5,
        container_6,
        container_7,
        container_8,
        container_9,
    ]
