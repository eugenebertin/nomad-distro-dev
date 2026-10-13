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


c.JupyterHub.spawner_class = LocalNORTHSpawner
