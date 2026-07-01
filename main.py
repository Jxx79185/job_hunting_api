from fastapi import FastAPI,HTTPException
from sqlalchemy import text
from database import engine
from pydantic import BaseModel
app=FastAPI()
companies=[
            {
                    'id':1,
                    'type':'システムエンジニア',
                    'name':'ITカンファー'
            },
            {
                    'id':2,
                    'type':'プログラマー',
                    'name':'シンアース'
            },
            {
                        'id':3,
                        'type':'エンジニア',
                     'name':'OZ MODE'
            }
        ]

class CompanyCreate(BaseModel):
    name:str
    type:str

@app.get('/')
def home():
    return {"message":"求职管理系统"}


@app.get('/companies')
def get_companies():
    with engine.connect() as connection:
        result = connection.execute(
            text('select id,name,type from companies')
        )
        rows=result.mappings().all()
        
    return [dict(row) for row in rows]
    

@app.get('/companies/search')
def search_company(keyword:str|None = None):
    if not keyword:
        return{
            'message':'请输入搜索关键词',
            'companies':[]
        }
    result=[]
    normalized_keyword=keyword.strip().lower()
    for company in companies:
        if (normalized_keyword in company['name'].lower() 
            or normalized_keyword in company['type'].lower()
            ):
            result.append(company)
    return{
                'keyword':keyword,
                'companies':result
            }

@app.get('/companies/{company_id}')
def get_company(company_id:int):
    with engine.connect() as connection:
        result=connection.execute(text(
            '''
            select id,name,type from companies
            where id = :company_id
            '''),
            {
                'company_id':company_id
            },
            )
        row = result.mappings().first()

        if row is None:
            raise HTTPException(
                status_code=404,
                detail='Company not found'
            )
        
    return dict(row)

@app.post('/companies')
def create_company(company:CompanyCreate):
    with engine.connect() as connection:
        reulst= connection.execute(
            text(
                '''
                insert into companies(name,type) 
                values(:name,:type)

                '''
            ),
            {
            "name":company.name,
            "type":company.type,
            }
        )

        connection.commit()
 
    return {
        'id':reulst.lastrowid,
        'name':company.name,
        'type':company.type
    }

@app.put('/companies/{company_id}')
def update_company(company_id:int,new_date:CompanyCreate):
    for company in companies:
        if company['id'] ==company_id:
            company['name']=new_date.name
            company['type']=new_date.type

            return company

    return {'error':'没有找到该公司'} 

@app.delete('/companies/{company_id}')
def delete_conpany(company_id:int):
    for company in companies:
        if company['id']==company_id:
            companies.remove(company)

            return {'message':'删除成功',
                    'company':company}
        
    raise HTTPException(status_code=404,detail='没有找到该公司')

@app.get('/profile')
def get_profile():
    return{
        'name':'JiangXuXin',
        'age':26
    }