import os
import torch
import torch.nn as nn

class DriverHMIAttentionModel(nn.Module):
    """車載HMI向けドライバー状態・注意監視モデル"""
    def __init__(self, input_dim=64, hidden_dim=32, output_dim=3):
        super(DriverHMIAttentionModel, self).__init__()
        self.fc1 = nn.Linear(input_dim, hidden_dim)
        self.relu = nn.ReLU()
        self.dropout = nn.Dropout(0.1)
        self.fc2 = nn.Linear(hidden_dim, output_dim)

    def forward(self, x):
        x = self.fc1(x)
        x = self.relu(x)
        x = self.dropout(x)
        x = self.fc2(x)
        return x

def main():
    print("=== SDV / HMI Edge AI: Quantization & ONNX Export Pipeline ===")
    
    # 1. HMIモデルの初期化
    model = DriverHMIAttentionModel()
    model.eval()
    print("1. 車載HMI向けモデルの初期化完了。")

    # 2. 成果物ディレクトリの作成
    output_dir = "output_artifacts"
    os.makedirs(output_dir, exist_ok=True)
    
    # PyTorch版（軽量化用）の保存
    torch.backends.quantized.engine = 'qnnpack'
    quantized_model = torch.quantization.quantize_dynamic(
        model, {nn.Linear}, dtype=torch.qint8
    )
    pt_path = os.path.join(output_dir, "hmi_driver_attention_quantized.pt")
    torch.save(quantized_model.state_dict(), pt_path)
    print(f"2-1. PyTorch量子化モデルを保存しました: {pt_path}")

    # --- 3. ONNXフォーマットへの変換（エッジ実機・推論用） ---
    # モデルの入力形状（バッチサイズ1、64次元の特徴量）に合わせたダミー入力を準備
    dummy_input = torch.randn(1, 64)
    onnx_path = os.path.join(output_dir, "hmi_driver_attention.onnx")
    
    torch.onnx.export(
        model,                  # 変換するモデル
        dummy_input,            # ダミー入力（形状確認用）
        onnx_path,              # 出力先パス
        export_params=True,     # 重みパラメータも含めて出力
        opset_version=14,       # ONNXのバージョン
        do_constant_folding=True, # 定数畳み込みによる最適化
        input_names=['input_features'],   # 入力層の名前
        output_names=['attention_scores'] # 出力層の名前
    )
    print(f"2-2. 車載エッジ用ONNXモデルを生成しました: {onnx_path}")

if __name__ == "__main__":
    main()
