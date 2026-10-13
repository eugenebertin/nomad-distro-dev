# Local override for JupyterHub in nomad-distro-dev
# Uses DummyAuthenticator so local development does not redirect to production Keycloak (nomad-lab.eu)

c.JupyterHub.authenticator_class = 'dummy'
c.Authenticator.auto_login = False
c.DummyAuthenticator.password = ''

