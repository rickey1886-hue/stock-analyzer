# stock-analyzer

Phase 1 MVPとして、米国株ティッカー（例: `AAPL`）と日本株ティッカー（例: `7203.T`）の分析を行うStreamlitアプリです。

> これは投資助言ではありません。最終判断は自己責任で行ってください。

## 実装済み

### Phase 1
- ティッカー入力
- 分析期間選択（1ヶ月 / 3ヶ月 / 6ヶ月 / 1年 / 3年 / 5年）
- 株価チャート（ローソク足、移動平均線、出来高）
- テクニカル指標（RSI、MACD、ボリンジャーバンド）
- 直近高値・安値
- ファンダメンタル取得（時価総額、PER、PBR、PSR、配当利回り、EPS、売上高、純利益、営業CF、FCF）
- 短期・中期・長期の補助判定
- 買い材料 / 売り材料・注意材料
- スコア内訳
- 判定（買い寄り / 中立 / 売り寄り）
- データ未取得項目一覧

### Phase 2-1 / Phase 2-2（今回追加）
- 市場指数の取得（APIキー不要 / yfinance）
  - S&P500 (`^GSPC`)
  - NASDAQ (`^IXIC`)
  - 日経平均 (`^N225`)
  - TOPIX (`^TOPX`)
  - SOX指数 (`^SOX`)
  - VIX指数 (`^VIX`)
  - ドル円 (`JPY=X`)
  - 原油価格 (`CL=F`)
- 個別株と市場指数の比較（選択期間騰落率）
  - 米国株: S&P500 / NASDAQ
  - 日本株: 日経平均 / TOPIX
  - 半導体関連の可能性が高い銘柄は SOX指数も参考表示
- UI追加
  - 市場指数一覧テーブル
  - 個別株 vs 市場指数の騰落率比較
  - 市場環境コメント
  - データ取得状況
- 補助的に「市場環境スコア」をスコア内訳へ表示（総合スコア本体は従来Phase 1ロジックのまま）

## 未実装（今後の拡張予定）

### Phase 2
- ニュース取得・センチメント分類
- SNS分析
- アナリスト予想
- 信用倍率、空売り比率
- イベントカレンダー
- セクター分析の深掘り

### Phase 3
- 需給（機関保有など）
- 高度なイベント連動分析
- 詳細なコンセンサス分析

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

## ローカル環境での動作確認手順（AAPL / NVDA / 7203.T / 9984.T）

1. アプリ起動

   ```bash
   streamlit run app.py
   ```

2. 以下ティッカーを順に入力して「分析開始」
   - `AAPL`
   - `NVDA`
   - `7203.T`
   - `9984.T`

3. 各ティッカーで次を確認
   - 既存Phase 1表示（チャート、テクニカル、ファンダメンタル、短中長期判定、買い/注意材料、スコア内訳）が維持
   - 市場環境セクションの追加表示
     - 市場指数一覧テーブル
     - 個別株 vs 市場指数の騰落率比較
     - 市場環境コメント
     - データ取得状況
   - 取得失敗データは「データ未取得」と表示され、アプリが停止しない

4. 必須文言の確認
   - 「これは投資助言ではありません。最終判断は自己責任で行ってください。」

## 注意事項
- データ取得には `yfinance` を利用しています。銘柄や時点により欠損する値があります。
- 取得失敗項目は推測せず「データ未取得」と表示します。
- 本ツールは投資判断の補助を目的としたもので、売買を推奨するものではありません。
