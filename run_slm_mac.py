import os
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["OMP_NUM_THREADS"] = "1"

import time
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

# 1. 使用するモデルの指定（車載エッジを想定した数BパラメータのSLM）
# Qwen2.5-3B-Instruct は軽量で日本語性能が高く、Macでもスムーズに動作します
model_id = "Qwen/Qwen2.5-3B-Instruct"

print("--- 1. トークナイザーの読み込み ---")
tokenizer = AutoTokenizer.from_pretrained(model_id)

print("--- 2. モデルのロード（Mac MPS / 半精度 float16） ---")
start_time = time.time()

# MacのMPS（Metal Performance Shaders）を利用するため device_map="mps" を指定
model = AutoModelForCausalLM.from_pretrained(
    model_id,
    torch_dtype=torch.float16,
    device_map="cpu"
)
load_time = time.time() - start_time
print(f"モデルロード完了時間: {load_time:.2f} 秒")

print("\n--- 3. 推論テスト（車載CANバス異常の解釈） ---")
prompt = "車載CANバスから 'Error Code: 0x4E2 (Brake Pressure Sensor Anomaly)' というログを受信しました。ドライバーへの適切な警告メッセージと、整備士向けの初期対応を簡潔に日本語で出力してください。"

messages = [
    {"role": "system", "content": "あなたは優秀な車載システムのAIアシスタントです。"},
    {"role": "user", "content": prompt}
]

# チャットテンプレートを適用してモデルに入力
text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
model_inputs = tokenizer([text], return_tensors="pt").to("cpu")

print("推論を実行中...")
start_gen = time.time()
generated_ids = model.generate(
    **model_inputs,
    max_new_tokens=256,
    temperature=0.1
)
gen_time = time.time() - start_gen

# 入力プロンプト部分を除いて出力結果だけをデコード
generated_ids = [
    output_ids[len(input_ids):] for input_ids, output_ids in zip(model_inputs.input_ids, generated_ids)
]
response = tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]

print(f"\n[推論結果]\n{response}")
print(f"\n生成時間: {gen_time:.2f} 秒")
