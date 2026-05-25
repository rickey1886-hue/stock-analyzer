# stock-analyzer

Phase 1 MVPとして、米国株ティッカー（例: `AAPL`）と日本株ティッカー（例: `7203.T`）の分析を行うStreamlitアプリです。

> これは投資助言ではありません。最終判断は自己責任で行ってください。

## 実装済み（Phase 1）
- ティッカー入力
- 分析期間選択（1ヶ月 / 3ヶ月 / 6ヶ月 / 1年 / 3年 / 5年）
- 株価チャート（ローソク足、移動平均線、出来高）
- テクニカル指標（RSI、MACD、ボリンジャーバンド）
- 直近高値・安値
- ファンダメンタル取得（時価総額、PER、PBR、PSR、配当利回り、EPS、売上高、純利益、営業CF、FCF）
- 簡易スコア
- 判定（買い寄り / 中立 / 売り寄り）
- 判定理由
- データ未取得項目一覧
- UI改善（サマリーカード、タブ整理、2カラム表示、見やすいスコア内訳・市場環境表示）

## 未実装（今後の拡張予定）
### Phase 2
- ニュース取得・センチメント分類
- 市場指数、金利、為替、VIX、原油との比較
- セクター分析

### Phase 3
- 需給（信用倍率、空売り比率、機関保有など）
- イベントカレンダー
- アナリスト予想・目標株価・コンセンサス
- SNS注目度分析

## ディレクトリ構成

```text
stock_analyzer/
  app.py
  requirements.txt
  README.md
  .env.example
  src/
    data/
      price_data.py
      fundamental_data.py
      market_data.py
      news_data.py
      event_data.py
    analysis/
      technical_analysis.py
      fundamental_analysis.py
      valuation_analysis.py
      sentiment_analysis.py
      scoring.py
    utils/
      ticker_utils.py
      config.py
      formatting.py
```

## セットアップ

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

## 起動方法

```bash
streamlit run app.py
```

ブラウザで表示されたURL（通常 `http://localhost:8501`）を開いて、ティッカーを入力し「分析開始」を押してください。

## ローカル環境での動作確認手順（AAPL / NVDA / 7203.T / 9984.T）

1. 仮想環境を有効化した状態でアプリを起動します。

   ```bash
   streamlit run app.py
   ```

2. 以下のティッカーを順番に入力して「分析開始」を押します。
   - `AAPL`
   - `NVDA`
   - `7203.T`
   - `9984.T`

3. 各ティッカーで次を確認します。
   - ローソク足・移動平均線・出来高が表示される
   - RSI / MACD / ボリンジャーバンドが表示される
   - 時価総額 / PER / PBR / PSR / 配当利回り / EPS / 売上高 / 純利益 / 営業CF / FCF が表示される（欠損時は「データ未取得」）
   - 簡易スコアと「買い寄り / 中立 / 売り寄り」判定が表示される
   - 判定理由とリスク要因、データ未取得項目一覧が表示される

4. 必須文言が画面に表示されることを確認します。
   - 「これは投資助言ではありません。最終判断は自己責任で行ってください。」

## 注意事項
- データ取得には `yfinance` を利用しています。銘柄や時点により欠損する値があります。
- 取得失敗項目は推測せず「データ未取得」と表示します。
- 本ツールは投資判断の補助を目的としたもので、売買を推奨するものではありません。
