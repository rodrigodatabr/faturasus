"""Importa todos os models para que o Alembic descubra os metadados automaticamente."""

from app.models.sigtap import (  # noqa: F401
    SigtapCid,
    SigtapDescricao,
    SigtapFinanciamento,
    SigtapFormaOrganizacao,
    SigtapGrupo,
    SigtapGrupoHabilitacao,
    SigtapHabilitacao,
    SigtapOcupacao,
    SigtapProcedimento,
    SigtapRegistro,
    SigtapRlProcCompativel,
    SigtapRlProcCid,
    SigtapRlProcHabilitacao,
    SigtapRlProcOcupacao,
    SigtapRlProcRegistro,
    SigtapRlProcServico,
    SigtapRubrica,
    SigtapServico,
    SigtapServicoClassificacao,
    SigtapSubgrupo,
)
from app.models.cnes import (  # noqa: F401
    CnesEstabelecimento,
    CnesHabilitacao,
    CnesProfissional,
    CnesServico,
)
from app.models.operacional import (  # noqa: F401
    EmbeddingProcedimento,
    FpoProgramacao,
    Profissional,
    RegistroProducao,
    StatusRegistro,
)
