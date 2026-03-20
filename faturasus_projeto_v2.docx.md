  
**FaturaSUS**  
Registro inteligente de produção ambulatorial

Scan do cartão SUS \+ áudio do procedimento \= BPA pronto

Projeto de Produto — DataBrasil Inteligência de Dados

Março 2026 — Versão 2.0  
*Documento confidencial*

# **Parte 1 — Discurso de vendas**

## **O problema**

Municípios brasileiros perdem milhões de reais por ano em repasses federais do SUS porque a produção ambulatorial de média e alta complexidade (MAC) não é registrada corretamente. O fluxo atual exige que o profissional de saúde anote o procedimento em papel, um digitador transcreva no sistema BPA-Magnético do DATASUS, e o gestor envie mensalmente os arquivos ao Ministério da Saúde. Cada elo dessa cadeia é uma oportunidade de perda.

A rotatividade nas equipes de faturamento é alta. O treinamento na tabela SIGTAP (com mais de 4.600 procedimentos) é demorado. O resultado: procedimentos realizados que nunca viram registro, registros com códigos errados que geram glosas, e um teto MAC que nunca é atingido — ou que, quando atingido, não pode ser comprovado para solicitar aumento.

## **O impacto financeiro**

| Exemplo real Uma policlínica que realiza 800 procedimentos ambulatoriais MAC por mês e registra apenas 500 está deixando de faturar até R$ 30.000/mês em produção aprovada — R$ 360.000/ano que o município poderia estar recebendo do governo federal. |
| :---- |

Mesmo quando o município já produz acima do teto MAC, o registro completo é essencial: é a evidência documental necessária para solicitar ao Ministério da Saúde o aumento do limite financeiro, via relatório técnico ou emenda parlamentar.

## **A solução: FaturaSUS**

FaturaSUS é um aplicativo móvel que permite ao profissional de saúde registrar um procedimento ambulatorial em 15 segundos, sem digitar nada. O profissional abre o app, escaneia o código de barras do Cartão SUS do paciente, e grava um áudio curto descrevendo o procedimento realizado. O sistema identifica o paciente automaticamente, classifica o procedimento na tabela SIGTAP, faz perguntas de confirmação se necessário, e registra tudo. No fim do mês, o responsável pelo faturamento confere e exporta o arquivo BPA pronto para importação no SIA/SUS.

## **Como funciona na prática**

1. **Scan:** O profissional aponta a câmera do celular para o código de barras do Cartão SUS. Em 1 segundo, o app identifica o paciente consultando a base nacional do CADSUS: nome, sexo, idade, município de residência. Na segunda consulta do mesmo paciente, basta dizer o nome.

2. **Áudio:** O profissional aperta o botão de microfone e diz: “Fiz uma videoColonoscopia, CID K63.5”. O sistema transcreve, identifica o código SIGTAP correto, e valida a compatibilidade com o CBO do profissional.

3. **Confirmação:** O bot apresenta o resumo na tela e, se necessário, faz perguntas: “Foi com biópsia?”. O profissional responde por botão, texto ou áudio. Quando tudo está completo, confirma com um toque.

4. **Pronto:** Quatro toques e um áudio. Todos os campos obrigatórios do BPA-I preenchidos. O digitador não é mais necessário.

## **Benefícios para o município**

* Aumento imediato do faturamento MAC sem aumentar a produção — apenas registrando o que já é feito

* Eliminação da dependência de digitadores especializados em SIGTAP

* Redução de glosas por codificação incorreta (a IA conhece as regras de compatibilidade)

* Dashboard de acompanhamento mensal: produzido vs. registrado vs. teto MAC

* Base documental robusta para solicitar aumento do teto MAC

* Transição suave para o CMD (Conjunto Mínimo de Dados) quando a fase 3 for obrigatória

* **Conformidade LGPD:** dados de saúde trafegam direto do celular para o servidor seguro, sem passar por plataformas de terceiros

## **Proposta de valor**

| ROI típico Investimento mensal de R$ 500–R$ 2.000 por unidade de saúde. Recuperação estimada de R$ 10.000–R$ 50.000/mês em produção subregistrada. ROI de 5x a 25x no primeiro mês. |
| :---- |

O FaturaSUS é oferecido como serviço mensal (SaaS), sem custo de implantação. O município não precisa instalar nada além do app no celular dos profissionais. O suporte inclui treinamento remoto da equipe e acompanhamento mensal de resultados.

# **Parte 2 — PRD simplificado**

## **1\. Visão do produto**

FaturaSUS é um app móvel (PWA) que combina leitura de código de barras do Cartão SUS, captura de áudio, inteligência artificial e integração com as APIs do DATASUS (CADSUS, SIGTAP, CNES) para registrar procedimentos ambulatoriais de média e alta complexidade de forma rápida e precisa. Gera o arquivo .txt no layout oficial do BPA para importação no SIA/SUS. Futuramente, enviará contatos assistenciais diretamente ao CMD via webservice da RNDS.

## **2\. Público-alvo**

**Usuário primário:** Médicos, enfermeiros e técnicos de saúde em policlínicas e ambulatórios de especialidades que realizam procedimentos de média e alta complexidade ambulatorial.

**Usuário secundário:** Responsável pelo faturamento da Secretaria Municipal de Saúde, que confere os registros e importa o arquivo no SIA.

**Decisor:** Secretário(a) Municipal de Saúde ou coordenador(a) de controle, avaliação e auditoria.

## **3\. Escopo do MVP**

| Foco do MVP Produção ambulatorial de média e alta complexidade (BPA-I), em unidades de saúde com maior volume de atendimentos especializados. Não inclui produção hospitalar (AIH) nem atenção básica. |
| :---- |

## **4\. Arquitetura técnica**

A arquitetura é composta por seis componentes principais:

| Componente | Tecnologia | Função |
| :---- | :---- | :---- |
| App móvel (PWA) | React/Next.js, html5-qrcode, MediaRecorder API | Interface principal: scanner de código de barras, gravação de áudio e chat conversacional |
| Identificação do paciente | API CADSUS v5 (webservice SOAP via RNDS) | A partir do CNS lido no código de barras, retorna nome, sexo, data nasc., município, nome da mãe |
| Transcrição de áudio | OpenAI Whisper API (GPT-4o Mini Transcribe) | Converte áudio em texto ($0,003/min) |
| Agente classificador | Claude API (Haiku) \+ base SIGTAP indexada | Identifica procedimento, desambigua, coleta campos faltantes via conversa |
| Banco de dados | PostgreSQL (Railway) | Armazena registros com todos os campos do BPA-I \+ histórico de pacientes já identificados |
| Exportação | Script Python | Gera arquivo .txt no layout oficial do BPA para importação no SIA/SUS |

## **5\. Interface do app**

A interface é uma tela única, dividida em três áreas:

**Topo — Botões de ação:** Dois botões grandes ocupam a parte superior da tela. O primeiro ativa o scanner de código de barras (câmera). O segundo ativa o microfone para gravação de áudio. São os únicos controles que o profissional precisa tocar na maioria dos atendimentos.

**Centro — Chat conversacional:** Uma área de conversa estilo mensageiro onde o bot exibe as informações extraídas, faz perguntas de desambiguação e apresenta o resumo do registro. Botões de resposta rápida inline (ex: “Sim / Não”, “Com biópsia / Sem biópsia”) permitem confirmar sem digitar. O histórico da conversa serve como log de auditoria para cada registro.

**Base — Campo de texto:** Para os casos em que o profissional preferir digitar em vez de gravar áudio, ou para correções pontuais.

## **6\. Fluxo do usuário**

5. **Cadastro inicial (única vez):** O gestor cadastra o profissional no sistema com seu CNS, CBO, CNES da unidade e nome. O profissional instala a PWA no celular (acessando um link, sem loja de apps) e faz login com suas credenciais.

6. **Scan do cartão SUS:** O profissional aperta o botão de scan e aponta a câmera para o código de barras do Cartão SUS. O app lê o CNS em tempo real (sem tirar foto), consulta a API CADSUS v5, e exibe no chat: “Paciente: Maria da Silva, F, 45 anos, Iguatama-MG”. O profissional confirma com um toque.

7. **Paciente recorrente (atalho):** Se o paciente já foi atendido antes, o profissional pode simplesmente dizer o nome no áudio (“paciente Maria da Silva”) e o sistema puxa o CNS do banco local. O scan só é necessário no primeiro atendimento.

8. **Gravação do procedimento:** O profissional aperta o botão de microfone e descreve o procedimento: “Fiz uma videoColonoscopia, CID K63.5”. O áudio vai direto do celular para o servidor (sem passar por plataformas de terceiros), é transcrito pelo Whisper, e o agente de IA classifica o procedimento na SIGTAP.

9. **Verificação e desambiguação:** O bot exibe no chat o que entendeu e valida as regras de negócio (compatibilidade CBO × procedimento, habilitação do CNES). Se faltar informação ou houver ambiguidade, pergunta com botões de resposta rápida: “Foi com biópsia? \[Sim\] \[Não\]”.

10. **Confirmação:** O bot mostra o resumo completo: paciente, procedimento, código SIGTAP, CID, data. O profissional toca em “Confirmar registro” (botão verde). O registro é salvo no banco de dados.

11. **Fechamento mensal:** O responsável pelo faturamento acessa o dashboard (web), confere os registros do mês, aprova e exporta o arquivo .txt no layout BPA.

12. **Importação no SIA:** O arquivo .txt é importado diretamente no SIA/SUS para processamento e envio ao DATASUS. O BPA-Magnético não é necessário como ferramenta de digitação.

## **7\. Identificação do paciente: três caminhos**

O campo mais crítico do BPA-I é o CNS do paciente (15 dígitos). O app oferece três métodos de captura, do mais rápido ao mais manual:

| Método | Como funciona | Quando usar |
| :---- | :---- | :---- |
| Scanner de código de barras | App lê o código de barras do Cartão SUS em tempo real. Consulta API CADSUS para puxar dados cadastrais. | Primeiro atendimento do paciente. Caminho mais rápido e à prova de erro. |
| Busca por nome (paciente recorrente) | Profissional diz o nome no áudio. Sistema busca no banco local de pacientes já identificados. | Pacientes que já foram atendidos antes. Dispensa o cartão físico. |
| Foto do cartão / tela do app Meu SUS Digital | OCR no número impresso ou exibido na tela. Fallback para quando o código de barras não funcionar. | Cartão danificado, ou paciente mostrando o app no celular. |

A consulta à API CADSUS v5 retorna automaticamente: nome completo, nome da mãe, sexo, data de nascimento, município de nascimento e município de residência. Esses são exatamente os campos de identificação do paciente exigidos pelo BPA-I, eliminando a necessidade de digitá-los manualmente.

## **8\. Campos do BPA-I coletados**

| Campo | Obrigatório | Fonte |
| :---- | :---- | :---- |
| Código SIGTAP do procedimento | Sim | Classificado pela IA a partir do áudio |
| CNS do profissional executante | Sim | Pré-cadastrado no perfil do app |
| CBO do profissional | Sim | Pré-cadastrado no perfil do app |
| CNES do estabelecimento | Sim | Pré-cadastrado no perfil do app |
| Data do atendimento | Sim | Automática (data do registro) ou informada |
| CNS do paciente | Sim | Scanner de código de barras \+ API CADSUS |
| Nome do paciente | Sim | API CADSUS (automático) |
| Sexo do paciente | Sim | API CADSUS (automático) |
| Data de nascimento | Sim | API CADSUS (automático) |
| Município de residência (IBGE) | Sim | API CADSUS (automático) |
| CID principal | Sim (BPA-I) | Informado no áudio ou perguntado pelo bot |
| Número de autorização | Condicional | Apenas para procedimentos que exigem autorização prévia |

| Preenchimento automático Dos 12 campos do BPA-I, 8 são preenchidos automaticamente (4 do perfil do profissional \+ 4 da API CADSUS). O profissional contribui efetivamente com 2 gestos: scan do cartão e áudio do procedimento. Os campos restantes (CID e autorização, quando aplicável) são extraídos do áudio ou perguntados pelo bot. |
| :---- |

## **9\. Regras de negócio críticas**

* O código SIGTAP informado deve ser compatível com o CBO do profissional executante (validado via API SIGTAP)

* O procedimento deve estar habilitado no CNES do estabelecimento (validado via API CNES)

* Não pode haver, na mesma competência, o mesmo procedimento registrado em BPA-C e BPA-I

* A data do atendimento deve estar dentro da competência de processamento (até 3 meses retroativos)

* A tabela SIGTAP local deve ser atualizada mensalmente (BDSIA)

* Revisão humana obrigatória antes da exportação do arquivo final

* O CNS do paciente deve ser validado na base do CADSUS antes de aceitar o registro

## **10\. APIs do DATASUS integradas**

O FaturaSUS integra com três webservices oficiais do DATASUS, disponíveis no barramento da RNDS. O acesso exige credenciamento do estabelecimento de saúde via Portal de Serviços do DATASUS (servicos-datasus.saude.gov.br):

| API | Função no FaturaSUS | Protocolo |
| :---- | :---- | :---- |
| CADSUS v5 | Identificar paciente a partir do CNS: retorna nome, sexo, data nasc., município, nome da mãe | SOAP (barramento RNDS) |
| SIGTAP | Validar código de procedimento, compatibilidade CBO, instrumento de registro, valores | SOAP (barramento RNDS) |
| CNES | Validar habilitações do estabelecimento, vínculos de profissionais, serviços cadastrados | SOAP (barramento RNDS) |

## **11\. Segurança e LGPD**

Dados de saúde são dados sensíveis sob a LGPD. O FaturaSUS adota as seguintes medidas:

* O áudio trafega diretamente do celular para o servidor na Railway via HTTPS, sem intermediários (diferente de soluções via WhatsApp, onde o áudio passa pelos servidores da Meta)

* O áudio é transcrito e descartado após a extração dos dados. Apenas o texto estruturado é armazenado

* O histórico do chat é mantido como log de auditoria, com registro de quem fez o quê e quando

* O acesso ao app exige autenticação do profissional, vinculada ao CNES do estabelecimento

* A base de dados fica em servidor no Brasil (Railway, região São Paulo)

* Base legal para tratamento: execução de políticas públicas (art. 7º, III e art. 11, II, “b” da LGPD)

## **12\. Cronograma estimado do MVP**

| Semana | Entrega | Responsável |
| :---- | :---- | :---- |
| 1–2 | Parser SIGTAP \+ base indexada no Postgres; integração API CADSUS v5 | Felipe (backend) \+ Claude Code |
| 2–3 | Agente conversacional: classificação SIGTAP, desambiguação, coleta de campos via chat | Rodrigo (prompt engineering) \+ Claude Code |
| 3–4 | App PWA: tela com scanner, microfone, chat; pipeline Whisper | Felipe (frontend) \+ Rodrigo (UX do fluxo) |
| 4–5 | Gerador de arquivo BPA .txt no layout oficial; validações SIGTAP/CNES | Rodrigo \+ Claude Code |
| 5–6 | Dashboard web: acompanhamento mensal, aprovação, exportação | Felipe (frontend) |
| 6–7 | Testes com dados reais de 1 unidade de saúde piloto | Rodrigo \+ equipe da SMS parceira |
| 7–8 | Ajustes, documentação, lançamento do piloto | Ambos |

## **13\. Custos estimados por município**

| Item | Custo mensal estimado | Observação |
| :---- | :---- | :---- |
| Whisper STT (500 áudios de 15s) | R$ 4–5 | \~125 min, $0,003/min |
| Claude API (500 classificações) | R$ 10–25 | Haiku/Sonnet conforme complexidade |
| APIs DATASUS (CADSUS, SIGTAP) | Gratuito | Webservices públicos do SUS |
| Railway (Postgres \+ backend \+ PWA) | R$ 30–50 | Compartilhado entre municípios |
| WhatsApp (notificações opcionais) | R$ 0–50 | Opcional, via Z-API ou similar |
| Total por município | R$ 50–130 | Margem para cobrar R$ 500–2.000/mês |

Nota: a mudança de WhatsApp para app próprio como canal principal reduziu o custo operacional por município de R$ 150–300 para R$ 50–130, eliminando a dependência da API do WhatsApp Business.

## **14\. Roadmap pós-MVP**

| Fase | Funcionalidade | Prazo estimado |
| :---- | :---- | :---- |
| Fase 2 | Integração CMD via webservice RNDS (quando fase 3 for obrigatória) | 2–4 semanas após regulamentação |
| Fase 3 | Modo lote: OCR de fichas de atendimento por foto | 4–6 semanas |
| Fase 4 | Relatório técnico automatizado para solicitação de aumento do teto MAC | 2–3 semanas |
| Fase 5 | Assistente para revisão de contas hospitalares (AIH) — produto separado | 8–12 semanas |
| Fase 6 | Integração com PEC (Pront. Eletrônico do Cidadão) / e-SUS APS | A avaliar |

## **15\. Riscos e mitigações**

| Risco | Prob. | Impacto | Mitigação |
| :---- | :---- | :---- | :---- |
| Erro de classificação SIGTAP | Média | Alto | Confirmação obrigatória no chat \+ revisão humana antes do envio |
| Ruído no áudio em ambiente hospitalar | Média | Médio | Confirmação textual \+ correções via botões de resposta rápida |
| Resistência dos profissionais | Alta | Médio | Onboarding com champion local \+ ROI visível no dashboard |
| Mudança regulatória (CMD fase 3\) | Baixa (CP) | Alto | Arquitetura dual-output (BPA \+ CMD) desde o início |
| Glosas por dados incompletos | Média | Alto | Validação via APIs DATASUS em tempo real \+ checklist pré-exportação |
| Indisponibilidade da API CADSUS | Baixa | Médio | Cache local de pacientes já consultados \+ fallback por OCR/nome |
| Adoção da PWA (instalação) | Média | Baixo | Instalação guiada na primeira visita; sem dependência de loja de apps |

## **16\. Métricas de sucesso**

| Métrica | Linha de base | Meta (3 meses) |
| :---- | :---- | :---- |
| Procedimentos registrados / realizados | \~60–70% | \>90% |
| Tempo médio de registro por procedimento | 5–10 min (digitador) | \<20 segundos (scan \+ áudio \+ confirmação) |
| Valor da produção aprovada no SIA (R$/mês) | Baseline do município | \+20–40% |
| Taxa de glosa nos registros gerados | Baseline do município | \<5% |
| Adoção (profissionais ativos / cadastrados) | N/A | \>70% |

## **17\. Sinergia com DataBrasil**

O FaturaSUS é complementar ao produto de relatórios de indicadores municipais da DataBrasil. Os dados de produção capturados pelo app alimentam diretamente os indicadores de saúde dos relatórios, criando um ciclo virtuoso:

* FaturaSUS captura a produção ambulatorial com mais precisão e velocidade

* Os relatórios DataBrasil mostram a evolução dos indicadores de saúde resultantes

* O dashboard de produção vs. teto MAC subsidia o relatório técnico para solicitar aumento do teto

* O prefeito enxerga resultado financeiro direto, fortalecendo a retenção de ambos os produtos