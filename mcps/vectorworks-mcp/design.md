# Vectorworks RAG + MCP (Local MVP) 開発要件

## 目的

- Vectorworks の Python/VectorScript ドキュメントをローカルで横断検索し、LLM から即参照できるようにする
- MCP (Model Context Protocol) ツール `vw.search` / `vw.answer` / `vw.get` を提供
- 簡易 Web UI（FastAPI 内）で検索・出典確認をブラウザから可能にする
  

## 構成

- **ingest**: md/html をチャンク化 → `sentence-transformers` で埋め込み → **FAISS** に格納
- **api**: FastAPI で `/search` `/answer` `/get` と UI を提供
- **mcp**: WebSocket MCP サーバー（JSON-RPC 2.0）。VS Code から接続可能

## 技術スタック

- Python 3.11, FastAPI, Uvicorn
- sentence-transformers (`all-MiniLM-L6-v2`)
- FAISS (cosine 相当；正規化内積)
- websockets, httpx, jinja2
- Docker / docker-compose

## データ仕様

- `data/`：原文の md/html。**相対パス**で `doc_id` として保存
- チャンク：目安 700 トークン（日本語 700–1000 字）、オーバーラップ 120
- `index/`：`vw.faiss` と `meta.jsonl`（`{doc_id, chunk_id, text}`）

## API

- `GET /search?q=...&k=6` → 上位 k チャンク（score/出典）
- `GET /answer?q=...&k=6` → 簡易ドラフト回答 + sources
- `GET /get?doc_id=...&chunk_id=...` → 原文チャンク

## MCP ツール

- `vw.search({ query, k? })`
- `vw.answer({ query, k? })`
- `vw.get({ doc_id, chunk_id })`

## 起動方法

```sh
docker compose up --build
# UI: http://localhost:8000
# MCP: ws://localhost:8765
# VS Code 追加:
code --add-mcp '{"name":"vw_docs_local","url":"ws://localhost:8765"}'
```

## データ取得（GitHub: vectorworks org 全件）

```sh
docker compose run --rm -e GITHUB_TOKEN="$GITHUB_TOKEN" app bash scripts/fetch_github_vectorworks.sh
# data/github/vectorworks/ 以下に各リポジトリを配置
```
