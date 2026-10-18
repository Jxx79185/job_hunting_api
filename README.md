# Job Hunting Management API

就職活動で応募した企業や選考状況を管理するためのWeb APIです。

複数の求人サイトで応募先や選考状況を管理するのは大変なため、PythonとFastAPIを学習しながら自分で管理できるAPIを作成しています。

## 使用技術

- Python 3.11
- FastAPI / Pydantic
- SQLAlchemy
- MySQL / MySQL Connector/Python
- python-dotenv
- Uvicorn
- pytest / FastAPI TestClient（テスト環境ではSQLiteを使用）

## 実装済みの機能

### 企業情報

- 登録・一覧取得・ID指定による取得・更新・削除
- 企業名・企業タイプによるキーワード検索

### 応募履歴

- 登録・一覧取得・ID指定による取得・更新・削除
- 企業名を含めて応募履歴を表示（`applications` と `companies` のJOIN）
- 企業名・応募職種・選考状況のキーワード検索
- 空白区切りの複数キーワード検索（全キーワードに一致するデータを取得）

### 入力チェック・エラー処理

- 企業名・企業タイプ・応募職種・選考状況の空欄／空白のみの入力を拒否
- これらの項目は、入力文字列の前後の空白を除去して保存
- 応募先企業IDは正の整数のみ受け付ける
- 入力内容に問題がある場合はHTTP `422`、対象データや参照先企業が存在しない場合はHTTP `404`を返す

## データベース

2つのテーブルを使用しています。

### companies

| カラム名 | 内容 |
|---|---|
| id | 企業ID |
| name | 企業名 |
| type | 企業タイプ |

### applications

| カラム名 | 内容 |
|---|---|
| id | 応募履歴ID |
| company_id | 応募先の企業ID |
| position | 応募職種 |
| application_status | 選考状況 |
| applied_date | 応募日 |
| job_url | 求人ページURL |
| notes | メモ |

`applications.company_id` から `companies.id` を参照します。

## API一覧

### 企業情報

| メソッド | URL | 内容 |
|---|---|---|
| GET | `/companies` | 一覧取得 |
| GET | `/companies/search?keyword=...` | キーワード検索 |
| GET | `/companies/{company_id}` | 1件取得 |
| POST | `/companies` | 登録 |
| PUT | `/companies/{company_id}` | 更新 |
| DELETE | `/companies/{company_id}` | 削除 |

### 応募履歴

| メソッド | URL | 内容 |
|---|---|---|
| GET | `/applications` | 一覧取得 |
| GET | `/applications?keyword=...` | キーワード検索 |
| GET | `/applications/{application_id}` | 1件取得 |
| POST | `/applications` | 登録 |
| PUT | `/applications/{application_id}` | 更新 |
| DELETE | `/applications/{application_id}` | 削除 |

以前の `GET /application/{application_id}`（単数形）は、`GET /applications/{application_id}` に統一しました。**旧URLを使うプログラムがある場合は変更してください。**

### 検索例

```text
GET /applications?keyword=エンジニア
GET /applications?keyword=エンジニア 一次面接
```

2番目の例は「エンジニア」と「一次面接」の両方を含む応募履歴を検索します。

## 起動方法

必要なライブラリをインストールします。

```bash
python -m pip install fastapi uvicorn sqlalchemy mysql-connector-python python-dotenv
```

プロジェクトフォルダに `.env` ファイルを作成します（このファイルはGitHubに公開しないでください）。

```env
DB_USER=your_user
DB_PASSWORD=your_password
DB_HOST=127.0.0.1
DB_PORT=3306
DB_NAME=job_hunting_db
```

MySQL側に上記2テーブルを準備した後、起動します。

```bash
python -m uvicorn main:app --reload --port 8001
```

Swagger UI: http://127.0.0.1:8001/docs

## 自動テスト

FastAPIの `TestClient` と `pytest` を使用して、APIの正常系・異常系を検証します。

```bash
python -m pip install pytest httpx
python -m pytest -q
```

テストは一時的なSQLiteデータベースを作成します。**通常使用するMySQLに接続せず、既存データも変更しません。** ただし、SQLiteでのテストが通ってもMySQL環境での動作を完全に保証するものではありません。

## 更新履歴

### 2026-10-18

- 応募履歴の詳細取得APIを `/applications/{application_id}` に統一
- 文字列の空白チェックと前後空白の除去を追加
- 応募先企業IDの入力チェックを追加
- 既存の `404` エラー処理を含む29ケースのAPIテストを追加
- READMEを現在の実装内容に合わせて更新

## 今後の改善候補

- APIレスポンス形式の統一
- ページネーション
- 詳細なログ処理
- MySQLを使用する統合テスト
