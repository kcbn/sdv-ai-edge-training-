# HMI Driver Copilot（実装リポジトリ）

計画: [docs/HMI-AI_30日統合計画.md](docs/HMI-AI_30日統合計画.md)  
役割: **Claude = 計画・レビュー / Cursor = 実装**

車載経路は操舵・制動に関与しない。Week 1 の Bedrock は開発用 API であり、`copilot/` からは呼ばない。

## 毎日

1. 計画の該当 Day を確認する（人が採択）
2. Cursor が許可リストの内側だけ実装する
3. ゲートを通す

```bash
source .venv/bin/activate
python -m pytest -q
python -m ruff check copilot tests dev_platform
python -m copilot --scene overload
python -m copilot --scene stable
python -m dev_platform --dry-run --text "少し眠い"
```

4. Claude または人が差分をレビューし、`dev` 向け PR にする（`main` へ直接載せない）

## 構成

| ディレクトリ | 役割 |
|--------------|------|
| `process/` | 人がオーナーの許可リスト・シーン・危害 |
| `copilot/` | エッジ小型ML（状態 → HMI許可アクション） |
| `dev_platform/` | Week1 開発基盤（Bedrock / Lambda ハンドラ） |
| `tests/` | 回帰。アクチュエータ禁則を含む |

## ブランチ

`main` = 動く安定版。`dev` で作業し、feature ブランチから PR。
