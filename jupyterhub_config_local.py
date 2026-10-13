from docker.types import DeviceRequest

with open("/srv/jupyterhub/jupyterhub_config.py") as config_file:
    exec(compile(config_file.read(), config_file.name, "exec"))


class LocalNORTHSpawner(NORTHSpawner):
    @functools.cached_property
    def profile_list(self):
        response = requests.get(f"{self.nomad_api_url}/north/tools/")
        response.raise_for_status()
        tools = response.json()

        if isinstance(tools, dict):
            tools = tools.get("data")
        if not isinstance(tools, list):
            raise ValueError("NOMAD /north/tools/ response must contain a tools list")

        return [
            Profile(
                display_name=tool["name"],
                description=tool["short_description"],
                slug=tool["name"],
                image=tool["image"],
                default_url=tool.get("default_url", "/lab"),
            )
            for tool in tools
        ]

    def apply_user_options(self, user_options):
        tool = user_options.get("tool")
        environment = user_options.get("environment")
        user_home = user_options.get("user_home")
        uploads = user_options.get("uploads")
        external_mounts = user_options.get("external_mounts")

        if not isinstance(tool, dict) or not tool.get("image"):
            raise ValueError("NOMAD launch options must include a tool image")
        if not isinstance(environment, dict):
            raise ValueError(
                "NOMAD launch options must include an environment mapping"
            )
        if not isinstance(user_home, dict):
            raise ValueError("NOMAD launch options must include a user_home mount")
        if not isinstance(uploads, list) or not isinstance(external_mounts, list):
            raise ValueError(
                "NOMAD launch options must include upload and external mount lists"
            )

        self.image = tool["image"]
        self.cmd = tool.get("cmd")
        self.default_url = tool.get("default_url", "/lab")
        self.privileged = tool.get("privileged", False)
        self.environment = environment

        mounts = [
            {
                "type": "bind",
                "source": user_home["host_path"],
                "target": user_home["mount_path"],
            }
        ]
        mounts.extend(
            {
                "type": "bind",
                "source": mount["host_path"],
                "target": mount["mount_path"],
                "read_only": mount.get("mode", "rw") != "rw",
            }
            for mount in uploads
        )
        mounts.extend(
            {
                "type": "bind",
                "source": mount["host_path"],
                "target": mount["bind"],
                "read_only": mount.get("mode", "ro") != "rw",
            }
            for mount in external_mounts
        )
        self.mounts = mounts

        host_config = dict(self.extra_host_config or {})
        security_opts = list(host_config.get("security_opt", []))
        if tool.get("seccomp_unconfined"):
            security_opts.append("seccomp:unconfined")
        if security_opts:
            host_config["security_opt"] = security_opts

        if tool.get("use_gpu"):
            device_requests = list(host_config.get("device_requests", []))
            device_requests.append(
                DeviceRequest(count=-1, capabilities=[["gpu"]])
            )
            host_config["device_requests"] = device_requests
        self.extra_host_config = host_config


c.JupyterHub.spawner_class = LocalNORTHSpawner
