# Visão Geral dos Scrapers

Este diretório lista diversos scrapers criados apenas para fins de demonstração. Cada arquivo Python é independente e exige as bibliotecas correspondentes instaladas previamente.

Para executar qualquer um deles:
1. Instale as dependências necessárias (Scrapy, requests, etc.).
2. Edite o script desejado para inserir chaves de API ou parâmetros corretos.
3. Execute `python nome_do_script.py`.

Abaixo está um resumo do propósito de cada scraper.

| Script | Finalidade |
| ------ | ---------- |
| `ScraperStack.py` | Coleta questões do StackOverflow via API. |
| `discord_data.py` | Exemplo de extração de mensagens do Discord. |
| `slack_data.py` | Exemplo de extração de mensagens do Slack. |
| `github_issues.py` | Coleta issues de um repositório GitHub. |
| `github_comments_data.py` | Coleta comentários de issues do GitHub. |
| `github_wiki_data.py` | Baixa conteúdo de wikis/documentações em repositórios GitHub. |
| `rfc_data.py` | Faz download de RFCs do IETF. |
| `jira_data.py` | Obtém issues de projetos JIRA. |
| `confluence_data.py` | Captura textos de páginas Confluence. |
| `devto_data.py` | Baixa artigos do Dev.to. |
| `docs_data.py` | Coleta conteúdo de documentação via Scrapy. |
| `Read_The_Docs_Data.py` | Spider para sites hospedados no ReadTheDocs. |
| `framework_docs_spider.py` | Spider para documentações de frameworks populares. |
| `generic_text_data.py` | Exemplo de uso de datasets da comunidade Hugging Face. |
| `kaggle_logs.py` | Procura datasets públicos contendo logs na Kaggle. |
| `kaggle_logs_processed.py` | Faz download e processa arquivos de log de um dataset da Kaggle. |
| `kaggle_logs_cli.py` | Busca datasets, baixa logs individuais via CLI. |
| `reddit_data.py` | Coleta posts e comentários do Reddit. |
| `oasst_data.py` | Baixa dados do conjunto de conversas OpenAssistant. |

**Observações**
- Cada script salva os dados em um arquivo JSON próprio.
- Alguns exemplos ao final dos arquivos incluem chamadas que exigem API keys. Ajuste conforme o seu ambiente antes de executar.
