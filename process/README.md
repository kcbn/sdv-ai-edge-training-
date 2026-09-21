# 開発プロセス

計画の本体は [docs/HMI-AI_30日統合計画.md](../docs/HMI-AI_30日統合計画.md)。  
Claude が計画・レビュー、Cursor が実装。

```
人が要件・安全・シーンを採択
    → Cursor が許可リストの内側だけ実装
    → ruff / pytest（必要なら python -m copilot）
    → Claude または人がレビュー
    → PR（dev → まとまったら main）
```

## 人とAI（統合計画 §6）

| 人が担う | Cursor が担う |
|----------|----------------|
| 要件定義・企画 | 実装 |
| 安全要件・リスク判断 | テスト生成 |
| アーキテクチャの最終承認 | ドキュメント下書き |
| 受け入れ判断 | 一次レビュー・定型リファクタ |

## 二つの実行経路（混ぜない）

| 経路 | 置き場 | LLM |
|------|--------|-----|
| 車載 HMI PoC | `copilot/` | 呼ばない。小型ML＋許可リスト |
| 開発基盤（Week1） | `dev_platform/` | AWS Bedrock（開発用）。車両制御JSONは拒否 |

## 安全境界

許可 HMI は `process/allowlist.json` の6アクションのみ。操舵・制動には関与しない。

- **H3 禁則語**: CI が `python -m copilot.safety` を実行し、採択済みシーンの出力 JSON に禁則アクチュエータ語と allowlist 外アクションがあれば落とす
- **許可リストの人レビュー**: `.github/CODEOWNERS` が `process/allowlist.json` 等を `@kcbn` 所有にする。GitHub の branch protection で **Require review from Code Owners** を `main` / `dev` に付ける（プロンプト制約の代替）
- **ゴールデンセット**: 今は `overload` と `stable` の2件。境界ケースは Week 2–3 で追加し、Week 4 統合評価の前に揃える

## 週次（統合計画）

| 週 | 完了の定義 | 今 |
|----|------------|----|
| 1 | GitHub + CI + Bedrock/Lambda の開発基盤 | Day4–6 |
| 2 | ASR/TTS。品質ゲートの再利用 | 未着手 |
| 3 | 量子化LLM（llama.cpp）＋対話RAG | 未着手 |
| 4 | 状態認識＋対話の統合 PoC と提案資料 | 未着手 |

変更の入口は `process/allowlist.json` と `process/scenes/`。`copilot/` から `dev_platform/` を import しない。
