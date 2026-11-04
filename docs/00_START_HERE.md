# VEXEL Jarvis — Issa Edition | Handoff de arranque

**Data:** 2026-11-04 | **Estado:** fundação remota em preparação; implementação/testes não concluídos.

## Decisões confirmadas
- **Base upstream escolhida:** [XtraWyze/Wyzer-Ai](https://github.com/XtraWyze/Wyzer-Ai), versão `v0.3.1`, commit **`db83c085feca32d3c091361165cb9ac7ecadafe0`**.
- **Identidade do produto derivado:** VEXEL Jarvis — Issa Edition. O nome, prompt, interacções e aspecto podem ser alterados; preservar avisos/licenças pertinentes.
- **IA em produção:** preferencialmente Ollama/modelos auto-hospedados, **sem API de inferência paga obrigatória**. Infraestrutura pode ter custos; não prometer cloud gratuito.
- **Língua prioritária:** português, incluindo uso natural de Moçambique. O upstream usa `small.en`/voz inglesa por defeito: PT **não está validado**.
- **Desenvolvimento/testes:** remotos, sem instalar/executar nada no computador do operador. Acesso ao PC do Issa indisponível até ao fim do dia e não é requisito para a primeira fase.
- **Segurança:** nenhuma operação irreversível ou de escrita real sem validação, aprovação e auditoria. O laboratório web apenas simula ferramentas de desktop.
- **Distribuição:** **não decidida** (local, servidor, híbrida). Um browser remoto sozinho não controla Windows do Issa.

## Onde está o trabalho
Este trabalho está no repositório **exclusivo** `rightware-corporations/jarvis`, na branch `main`. Este repositório é **público**: não publicar credenciais, dados pessoais reais, gravações ou segredos. Não utilizar `rightware-corporations/vexel` nem `vexel-website` para o Jarvis.

## Leitura na ordem certa
1. `01_CURRENT.md`: estado exacto e limites.
2. `02_ARCHITECTURE.md`: separação núcleo, laboratório web e agente Windows.
3. `03_BACKLOG.md`: ordem de execução P0/P1/P2/P3.
4. `04_ACCEPTANCE.md`: evidências de aceitação e gate de entrega.

## Regras
- Não confundir **documentado**, **identificado em código**, **testado** e **aceite**.
- Não modificar o repositório `rightware-corporations/vexel` nem o website.
- Não transformar Claude/ChatGPT em dependência da inferência final.
- Não importar modelos de wake word, vozes e artefactos com direitos não verificados.
- Não instalar no PC do operador ou do Issa sem consentimento específico; na fase actual, só remoto.
- Preservar proveniência dos ficheiros upstream e respetiva licença.
