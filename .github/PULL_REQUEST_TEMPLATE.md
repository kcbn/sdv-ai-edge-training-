## プロセス確認（HMI-AI 30日統合計画）

- [ ] 該当 Day は `docs/HMI-AI_30日統合計画.md` と一致する
- [ ] `process/allowlist.json` の変更は人が採択した
- [ ] 車載経路（`copilot/`）から Bedrock / `dev_platform` を呼んでいない
- [ ] 出力にアクチュエータ指令がない
- [ ] PR の CI は ruff + pytest のみ（AWS デプロイなし）
- [ ] マージ先はまず `dev`（`main` へ直接載せない）
