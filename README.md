# Job Hunting Management API

就職活動で応募した企業や選考状況を管理するためのAPIです。

複数の求人サイトを使っていると、応募した企業や現在の選考状況が分かりにくくなるため、自分で管理できるものを作ろうと思い、開発を始めました。

現在はFastAPIとMySQLを勉強しながら開発しています。

## 使用技術

- Python 3.11
- FastAPI
- Pydantic
- SQLAlchemy
- MySQL
- MySQL Connector/Python
- python-dotenv
- Uvicorn

## 現在実装している機能

### 企業情報

- 企業情報の登録
- 企業一覧の取得
- IDによる企業情報の取得
- 企業情報の更新
- 企業情報の削除
- 企業名、企業タイプによる検索

### 応募履歴

- 応募履歴の登録
- 応募履歴一覧の取得
- 企業名を含めた応募履歴の表示
- 企業名、応募職種、選考状況によるキーワード検索
- 空白で区切った複数キーワードによる検索

応募履歴を取得するときは、`applications` テーブルと `companies` テーブルをJOINして、企業名も一緒に取得しています。

複数のキーワードを入力した場合は、現在はすべてのキーワードに一致するデータを検索します。

## データベース

現在は2つのテーブルを使用しています。

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
| job_url | 求人ページのURL |
| notes | メモ |

`applications.company_id` は `companies.id` を参照しています。

## API

### 企業情報

| メソッド | URL | 内容 |
|---|---|---|
| GET | `/companies` | 企業一覧を取得 |
| GET | `/companies/search?keyword=...` | 企業を検索 |
| GET | `/companies/{company_id}` | 企業情報を1件取得 |
| POST | `/companies` | 企業情報を登録 |
| PUT | `/companies/{company_id}` | 企業情報を更新 |
| DELETE | `/companies/{company_id}` | 企業情報を削除 |

### 応募履歴

| メソッド | URL | 内容 |
|---|---|---|
| GET | `/applications` | 応募履歴一覧を取得 |
| GET | `/applications?keyword=...` | 応募履歴を検索 |
| POST | `/applications` | 応募履歴を登録 |

## 検索例

```text
GET /applications?keyword=エンジニア
```

企業名、応募職種、選考状況の中から検索します。

複数のキーワードを検索する場合は、空白で区切ります。

```text
GET /applications?keyword=エンジニア 一次面接
```

この場合は、「エンジニア」と「一次面接」の両方に一致する応募履歴を取得します。

## 起動方法

必要なライブラリをインストールします。

```bash
python -m pip install fastapi uvicorn sqlalchemy mysql-connector-python python-dotenv
```

プロジェクトのフォルダに `.env` ファイルを作成します。

```env
DB_USER=your_user
DB_PASSWORD=your_password
DB_HOST=127.0.0.1
DB_PORT=3306
DB_NAME=job_hunting_db
```

サーバーを起動します。

```bash
python -m uvicorn main:app --reload --port 8001
```

Swagger UI：

```text
http://127.0.0.1:8001/docs
```

## 開発中の機能

- IDによる応募履歴の取得
- 応募履歴の更新
- 応募履歴の削除

まだ開発途中のため、今後も機能を追加していく予定です。
