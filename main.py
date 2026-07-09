from fastapi import FastAPI,HTTPException
from sqlalchemy import text
from database import engine
from pydantic import BaseModel
from datetime import date

app=FastAPI()

class CompanyCreate(BaseModel):
    name:str
    type:str

class ApplicationCreate(BaseModel):
    company_id:int
    position:str
    application_status:str
    applied_date:date | None = None
    job_url:str | None = None
    notes:str |None = None


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

@app.post('/applications')
def create_application(application:ApplicationCreate):
    with engine.connect() as connection:
        company_result=connection.execute(
            text(
                '''
                select id from companies
                where id =:company_id
                '''),
                {
            'company_id':application.company_id
        }
        )
        company_row = company_result.mappings().first()

        if company_row is None:
            raise HTTPException(
                status_code=404,
                detail='Company not found'
            )


        result=connection.execute(text(
            '''
            insert into applications(
            company_id,
            position,
            application_status,
            applied_date,
            job_url,
            notes
            )
            values(
            :company_id,
            :position,
            :application_status,
            :applied_date,
            :job_url,
            :notes)
            '''
        ),
        {
            'company_id': application.company_id,
            'position': application.position,
            'application_status': application.application_status,
            'applied_date': application.applied_date,
            'job_url': application.job_url,
            'notes': application.notes,
        }
        )
        connection.commit()
        new_id = result.lastrowid

        return{
            'company_id': application.company_id,
            'position': application.position,
            'application_status': application.application_status,
            'applied_date': application.applied_date,
            'job_url': application.job_url,
            'notes': application.notes,
            }

@app.get('/applications')
def get_applications(keyword:str | None = None):
    print("新版 GET /applications 被执行了")
    sql = '''
            select
            applications.id,
            applications.company_id,
            companies.name as company_name,
            applications.position,
            applications.application_status,
            applications.applied_date,
            applications.job_url,
            applications.notes
            from applications
            join companies
                on applications.company_id=companies.id
                '''
        
    conditions = []
    parameters = {}
    
    if  keyword and keyword.strip():
        keywords = keyword.strip().lower().split()

        for index,word in enumerate(keywords):
            parameters_name = f'keyword_{index}'

            conditions.append(f'''(
                              lower(companies.name) like :{parameters_name}
                              or lower(applications.position) like :{parameters_name}
                              or lower(applications.application_status) like :{parameters_name})''')
            
            parameters[parameters_name]=f'%{word}%'

    if conditions:
        sql += '\nwhere' + '\nand'.join(conditions)

    sql +='\norder by applications.id desc'

    with engine.connect() as connection:
        query_result = connection.execute(
        text(sql),
        parameters,
    )

        rows = query_result.mappings().all()

    response = {
    "applications": [dict(row) for row in rows]
    }

    print("rows =", rows)
    print("response =", response)

    return response

@app.get('/application/{application_id}')
def get_application(application_id:int):
    with engine.connect() as connection:
        application_result=connection.execute(text(
            '''
            select applications.id,
            applications.company_id,
            companies.name as company_name,
            applications.position,
            applications.application_status,
            applications.applied_date,
            applications.job_url,
            applications.notes
            from applications
            join companies
                on applications.company_id = companies.id
            where applications.id = :applications_id
            '''
            
        ),
            {'applications_id': application_id} 
        )

        row = application_result.mappings().first()
    if row is None:
        raise HTTPException(
            status_code=404,
            detail='Application not found')
    
    return dict(row)




@app.put('/applications/{application_id}')
def update_application(application_id:int,application:ApplicationCreate):
    with engine.connect() as connection:
        application_result=connection.execute(
            text(
                '''select id from applications
                where id=:application_id'''
              
            ),  
            {
                'application_id':application_id
            }
        )
        application_row=application_result.mappings().first()

        if application_row is None:
            raise(HTTPException(
                status_code=404,
                detail='Application not found'
            ))

        company_result=connection.execute(
            text(
                '''select companies.id from companies
                where companies.id=:company_id'''
            ),
            {
                'company_id':application.company_id
            }
        )

        company_row=company_result.mappings().first()

        if company_row is None:
            raise(HTTPException(
                status_code=404,
                detail='Company not found'
            ))

        connection.execute(text(
            '''
            update applications
            set 
            company_id=:company_id,
            position=:position,
            application_status=:application_status,
            applied_date=:applied_date,
            job_url=:job_url,
            notes=:notes
            where id=:application_id
            '''
        ),
        {
            'company_id':application.company_id,
            'position':application.position,
            'application_status':application.application_status,
            'applied_date':application.applied_date,
            'job_url':application.job_url,
            'notes':application.notes,
             "application_id": application_id
        })

        connection.commit()

        return {
            'id':application_id,
            'company_id':application.company_id,
            'position':application.position,
            'application_status':application.application_status,
            'applied_date':application.applied_date,
            'job_url':application.job_url,
            'notes':application.notes
            }

@app.delete('/applications/{application_id}')
def delete_application(application_id:int):
    with engine.connect() as connection:
        result = connection.execute(
            text(
                '''
                select id from applications
                where id=:application_id
                '''
            ),
            {
                'application_id':application_id
            }
        )

        row= result.mappings().first()

        if row is None:
            raise HTTPException(
                status_code=404,
                detail='Application not found'
            )
            
        connection.execute(
            text(
                '''
                    delete from applications
                    where id=:application_id
                '''
            ),
            {
                'application_id':application_id
            }
        )

        connection.commit()

        return {'message':'Application was deleted',
                'application_id':application_id}

@app.get('/profile')
def get_profile():
    return{
        'name':'JiangXuXin',
        'age':26
    }