import os
import torch
import torch.nn as nn

class DriverHMIAttentionModel(nn.Module):
    """
    【車載HMI向け実用例】ドライバーの状態・注意監視モデル
    - 入力: 車載IRカメラから抽出された顔のランドマークや特徴量ベクトル（例: 64次元）
    - 出力: ドライバーの状態分類（例: 3クラス [1: 前方注視, 2: わき見, 3: 居眠り兆候]）
    """
    def __init__(self, input_dim=64, hidden_dim=32, output_dim=3):
        super(DriverHMIAttentionModel, self).__init__()
        # エッジデバイス（車載ECU）の限られたメモリ・演算リソースを考慮したコンパクトな設計
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
    print("=== SDV / HMI Edge AI Model Quantization Pipeline ===")
    
    # PyTorchの量子化エンジンの指定（CPU環境向け）
    torch.backends.quantized.engine = 'qnnpack'
    
    # 1. HMIモデルの初期化
    model = DriverHMIAttentionModel()
    model.eval()
    print("1. 車載HMI向けドライバー状態検知モデルの初期化が完了しました。")

    # 2. 動的量子化（Dynamic Quantization）の適用
    # float32からint8へ量子化することで、車載エッジでのメモリフットプリントと推論負荷を大幅に削減
    quantized_model = torch.quantization.quantize_dynamic(
        model, 
        {nn.Linear}, 
        dtype=torch.qint8
    )
    print("2. モデルのINT8量子化（エッジ軽量化）が正常に完了しました。")

    # 3. 成果物ディレクトリの作成とモデルの保存
    output_dir = "output_artifacts"
    os.makedirs(output_dir, exist_ok=True)
    
    model_path = os.path.join(output_dir, "hmi_driver_attention_quantized.pt")
    torch.save(quantized_model.state_dict(), model_path)
    print(f"3. 軽量化されたHMIモデルを保存しました: {model_path}")

if __name__ == "__main__":
    main()
