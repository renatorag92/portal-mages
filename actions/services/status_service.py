import webcolors
from django.core.exceptions import ValidationError

from ..repositories.status_repositorio import StatusRepositorio

PT_EN = dict(zip(
    'azul vermelho verde amarelo laranja roxo rosa preto branco cinza marrom ciano dourado prata turquesa bege lilás violeta magenta índigo salmão coral vinho lima'.split(),
    'blue red green yellow orange purple pink black white gray brown cyan gold silver turquoise beige lavender violet magenta indigo salmon coral maroon lime'.split(),
))
EN_PT = {ingles: portugues for portugues, ingles in PT_EN.items()}


class StatusService:
    @staticmethod
    def buscar_ou_404(status_id):
        return StatusRepositorio.buscar_ou_404(status_id)

    @staticmethod
    def listar_todos():
        return StatusRepositorio.listar_com_contagem()

    @staticmethod
    def cor_para_edicao(status):
        if status.cor_nome:
            return status.cor_nome
        try:
            nome_cor = webcolors.hex_to_name(status.cor)
        except ValueError:
            return status.cor
        return EN_PT.get(nome_cor, nome_cor)

    @staticmethod
    def normalizar_cor(cor_informada):
        cor = PT_EN.get(cor_informada.lower(), cor_informada.lower())
        try:
            return webcolors.name_to_hex(cor)
        except ValueError:
            try:
                return webcolors.normalize_hex(cor)
            except ValueError:
                raise ValidationError(
                    'Cor inválida. Use um nome (ex.: amarelo) ou hexadecimal (ex.: #ffff00).'
                )

    @staticmethod
    def cor_em_uso(cor, excluir_pk=None):
        return StatusRepositorio.cor_existe(cor, excluir_pk)