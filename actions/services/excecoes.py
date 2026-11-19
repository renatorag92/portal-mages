class ErroRegraNegocio(Exception):
    def __init__(self, mensagem, status=400, errors=None):
        super().__init__(mensagem)
        self.mensagem = mensagem
        self.status = status
        self.errors = errors