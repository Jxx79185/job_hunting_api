from fastapi import FastAPI,HTTPException
from sqlalchemy import text
from database import engine
from pydantic import BaseModel
app=FastAPI()

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
    if not keyword or not keyword.strip():
        return{
            'message':'请输入搜索关键词',
            'companies':[]
        }

    normalized_keyword=keyword.strip().lower()
    search_pattern = f'%{normalized_keyword}%'

    with engine.connect() as connection:
        result=connection.execute(
            text(
                '''select id,name,type
                from companies
                where lower(name) like :keyword
                or lower(type) like :keyword'''
            ),
            {
                'keyword':search_pattern
                }

        )

        rows = result.mappings().all()
        
    return {'keyword':keyword,
            'companies':[dict(row) for row in rows]}

@app.get('/companies/{company_id}')
def get_company(company_id:int):
    with engine.connect() as connection:
        result=connection.execute(text(
            '''
            select id,name,type 
            from companies
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
        result= connection.execute(
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
        new_id = result.lastrowid
    return {
        'id':new_id,
        'name':company.name,
        'type':company.type
    }

@app.put('/companies/{company_id}')
def update_company(company_id:int,new_data:CompanyCreate):
    with engine.connect() as connection:
        result=connection.execute(
            text(
                '''
                select id
                from companies
                where id = :company_id
                '''
            ),
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
        
        connection.execute(
            text(
            '''
            update companies 
            set name =:name,
                type =:type
            where id = :company_id
            '''),
            {'name':new_data.name,
             'type':new_data.type,
             'company_id':company_id
             }
        )
        connection.commit()
    return {
        'id':company_id,
        'name':new_data.name,
        'type':new_data.type,
    }

@app.delete('/companies/{company_id}')
def delete_conpany(company_id:int):
    with engine.connect() as connection:
        result=connection.execute(
                text(
                '''
                select id from companies
                where id=:company_id
                '''
                ),
                {
                'company_id':company_id
                }
                )
        row = result.mappings().first()
        if row is None:
            raise HTTPException(
                status_code=404,
                detail='没有找到该公司'
                )

        connection.execute(
            text(
                '''
                delete from companies
                where id = :company_id
                '''
            ),
            {
                'company_id':company_id
            }
        )
        
        connection.commit()

    return{
        'message':'Company deleted',
        'id':company_id
    }
@app.get('/profile')
def get_profile():
    return{
        'name':'JiangXuXin',
        'age':26
    }