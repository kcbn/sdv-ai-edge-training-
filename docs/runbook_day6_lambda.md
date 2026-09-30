# Day 6 Lambda デプロイ記録（人が記入）

開発経路 `dev_platform/` だけを zip にして手動アップロードする。車載経路 `copilot/` は含めない。値はコンソールで確定したあと、この表に人が書く。

## 成果物

```bash
source .venv/bin/activate
bash scripts/package_lambda.sh
```

生成物: `build/lambda.zip`（gitignore。リポジトリには載せない）

ハンドラ想定: `dev_platform.lambda_handler.handler`  
`DRY_RUN` はリクエストボディではなく Lambda 環境変数で与える。

## 記録欄


| 項目                         | 値                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |
| -------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 関数名                        | hmi-dev-chat                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       |
| 関数ARN                      | arn:aws:lambda:ap-southeast-2:<ACCOUNT_ID>:function:hmi-dev-chat                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   |
| ランタイム | Python 3.11 |
| アーキテクチャ | x86_64 |
| ハンドラ | `dev_platform.lambda_handler.handler` |
| タイムアウト | 30秒（既定3秒ではBedrock応答に足りない） |
| メモリ | 128MB |
| 予約同時実行数 | 1（誤呼び出し時の課金上限） |
| 環境変数 | `DRY_RUN=1`, `BEDROCK_MODEL_ID=amazon.nova-micro-v1:0`（2026-09-30 Claude 3 Haikuから変更）<br>`AWS_REGION` はLambda予約変数のため設定しない |
| IAMロール名 | hmi-dev-lambda-role（`AWSLambdaBasicExecutionRole` + インライン `bedrock-invoke-nova-micro`） |
| IAMロールARN                  | arn:aws:iam::<ACCOUNT_ID>:role/hmi-dev-lambda-role                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| インラインポリシーJSON | `bedrock-invoke-nova-micro`：`{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Action":"bedrock:InvokeModel","Resource":"arn:aws:bedrock:ap-southeast-2::foundation-model/amazon.nova-micro-v1:0"}]}`<br>2026-09-30：Claude 3 Haiku提供終了のため `bedrock-invoke-haiku` を削除して置き換え |
| API Gateway ID・ルート・スロットリング | HTTP API `hmi-dev-chat-api`（ID: `<api-id>`、`aws apigatewayv2 get-apis` で確認可）/ `POST /chat` のみ → `hmi-dev-chat`（AWS_PROXY、ペイロード2.0）/ `$default` ステージ自動デプロイ / スロットリング レート1・バースト2 / 認証なし（公開中は `DRY_RUN=1` を維持） |
| Lambdaリソースベースポリシー | `apigateway.amazonaws.com` に `lambda:InvokeFunction` を許可。SourceArn は `<api-id>/*/*/chat` に限定（コンソールが自動作成） |
| 確認日と結果 | 2026-09-30 テストイベント3件（`normal`／`vehicle-control`／`empty`）すべて期待どおり（DRY_RUN=1）<br>2026-09-30 `DRY_RUN=0` で実呼び出し→失敗。`ResourceNotFoundException: This model version has reached the end of its life`（Claude 3 Haiku 提供終了）。定型文フォールバックとCloudWatchへのログ出力は想定どおり動作、発話はログに出ていない。IAMを `bedrock-invoke-nova-micro` に差し替え済み<br>2026-09-30 Nova Microで `DRY_RUN=0` 実呼び出し1回→成功（200、`intent: suggest`、`vehicle_command: null`、`blocked: false`、モデル生成の日本語返答）。直後に `DRY_RUN=1` へ戻したことをCLIで確認<br>2026-09-30 API Gateway経由のcurl 3件すべて期待どおり（`POST /chat` 通常→200・`dry_run: true`／`POST /chat` 車両操作→200・`blocked: true`／`GET /chat`→`Not Found`）。設定値はCLIで照合済み |


