from fastapi import FastAPI, WebSocket, Request, Depends, HTTPException, status
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, Response
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.templating import Jinja2Templates

from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from pydantic import BaseModel

from jose import JWTError, jwt
from passlib.context import CryptContext

from datetime import datetime, timedelta

from io import StringIO

from alarms.management import AlarmSystem

import json
import os
import asyncio
import pandas as pd


SECRET_KEY = "b161b7a66ffeb5e6f425576b64461e054afa43766d7894d697b3498ec6c6d988"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(
    schemes=['bcrypt'],
    deprecated="auto"
)
oaut_2_scheme = OAuth2PasswordBearer(tokenUrl='token')
app = FastAPI()

app.mount("/static", StaticFiles(directory=os.path.join("static")), name="static")

templates = Jinja2Templates(directory="templates")

Base = declarative_base()
engine = create_engine("sqlite:///traffic_control.db")
Session = sessionmaker(bind=engine)


pattern = '%d-%m-%Y-%H-%M-%S'
initial_time = datetime.now().strftime(pattern)
alarm_system = AlarmSystem(
    carril_izq_threshold=13,
    carril_der_threshold=22
)


# PyDantic Models

class Data(BaseModel):
    name: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: str or None = None


class UserPydantic(BaseModel):
    username: str
    hashed_password: str

class AlarmData(BaseModel):
    identifier: str
    action: str

class DayData(BaseModel):
    day_str: str

# Database Tables

class TrafficRecord(Base):
    __tablename__ = "traffic_record"

    id = Column(Integer, primary_key=True)
    timestamp = Column(String)
    carril_izq = Column(Integer)
    carril_der = Column(Integer)

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String)
    hashed_password = Column(String)

class Alarm_Event(Base):
    __tablename__ = "alarms"

    id= Column(Integer, primary_key= True)
    alarm_identifier= Column(String)
    timestamp= Column(String)
    priority= Column(String)

class Log(Base):
    __tablename__ = "logs"

    id= Column(Integer, primary_key= True)
    description= Column(String)
    timestamp=Column(String)

Base.metadata.create_all(bind=engine)

# Auth handling functions

def verify_password(plaintext_pswd: str, hashed_pswd: str):
    return pwd_context.verify(plaintext_pswd, hashed_pswd)

def get_password_hash(password: str):
    return pwd_context.hash(password)

def get_user(username:str):
    with Session() as db:
        user = db.query(User).filter(User.username == username).first()
        if user is not None:
            user = UserPydantic(
                username= user.username,
                hashed_password= user.hashed_password
            )
            return user
        else:
            raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not registered"
        )

def authenticate_user(username:str, password:str):
    user = get_user(username)

    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    
    return user

def create_access_token(user: UserPydantic, expires_delta: timedelta or None = None):
    to_encode = {
        'sub': user.username,
        'hashed_password': user.hashed_password,
    }

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=120)
 
    to_encode.update({'exp': expire})

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    return encoded_jwt

async def get_current_user (token:str = Depends(oaut_2_scheme)):
    credential_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail='Could not validate credentials',
        headers={
            "WWW-Authenticate": "Bearer"
        }
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")

        if username is None:
            print("username was none")
            raise credential_exception
        
        token_data = TokenData(username=username)
    except JWTError:
        print("jwterror")
        raise credential_exception
    user = get_user(username=token_data.username)

    if user is None:
        print("user was none")
        raise credential_exception
    
    return user
        

async def get_current_active_user(current_user: UserPydantic = Depends(get_current_user)):
    
    return current_user

# Endpoints

@app.post('/token', response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    
    user = authenticate_user(form_data.username, form_data.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        user= user,
        expires_delta=access_token_expires

    )

    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/users/me/", response_model=UserPydantic)
async def read_users_me(current_user: UserPydantic = Depends(get_current_active_user)):
    return current_user

@app.post('/create/')
async def create_user(usern:str, password:str):
    with Session() as db:
        new_user = User(
            username = usern,
            hashed_password = get_password_hash(password)
        )
        db.add(new_user)
        db.commit()

        return {"message": f"User {new_user.username} created successfully"}
    
@app.get("/login")
async def login_page(request: Request):
    context = {
        'site': 'STLight',
        'logo': 'static/images/logo.jpeg',
        'title': 'Login',
        'request': request,
    }

    return templates.TemplateResponse('login.html', context=context)

@app.websocket("/websocket")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    try:
        while True:
            with Session() as db:
                try:
                    traffic_record: TrafficRecord = db.query(TrafficRecord).order_by(TrafficRecord.id.desc()).first()

                    if traffic_record is None:
                        # Not sending any data
                        continue

                    data_points = db.query(TrafficRecord).all()
                    data_points = [{
                            'ts': dp.timestamp,
                            'carril_izq': dp.carril_izq,
                            'carril_der': dp.carril_der,
                        } for dp in data_points]
                    if len(data_points) > 10:
                        data_points = data_points[-10:]
                except Exception as e:
                    print(e)

                raised_alarms = []

                if traffic_record:
                    
                    raised_alarms = alarm_system.detect_traffic_jam((
                            traffic_record.carril_izq,
                            traffic_record.carril_der
                        ))

                sensor_communication_checks = [
                    ('COM-CV0', 'Subsistema de Visión', True),
                    ('COM-HT0', 'Sensor de temperatura/humedad relativa', False),
                ]

                for ident, name, priority in sensor_communication_checks:
                    new_alarm = alarm_system.detect_sensor_disconnection(
                        ts=traffic_record.timestamp,
                        pattern=pattern,
                        identifier=ident,
                        name=name,
                        priority=priority
                    )

                    alarm_system.detect_sensor_reconnection(
                        ts=traffic_record.timestamp,
                        pattern=pattern,
                        identifier=ident
                    )

                    if new_alarm:
                        raised_alarms.append(new_alarm)
                
                alarm_system.check_progression()
                
                for a in raised_alarms:
                    new_alarm_event = Alarm_Event(
                        alarm_identifier= a.identifier,
                        timestamp= datetime.now().strftime(pattern),
                        priority= a.priority
                    )

                    msg = Log(
                        description= f"{a.identifier}: alarma registrada",
                        timestamp= datetime.now().strftime(pattern)
                    )

                    db.add(new_alarm_event)
                    db.commit()

                    db.add(msg)
                    db.commit()

                # Getting active alarms
                alarms = alarm_system.active_alarms(mode='json')
                alarms = [json.loads(a) for a in alarms]

                # Getting the last ten alarm records
                alarm_records = db.query(Alarm_Event).all()
                alarm_records = [ {
                    'identifier': a.alarm_identifier,
                    'ts': a.timestamp,
                    'priority': a.priority
                } for a in alarm_records]
                if len(alarm_records) > 10:
                    alarm_records = alarm_records[-10:]

                # Getting the last ten logs
                logs = db.query(Log).all()
                logs = [ {
                    'description': l.description,
                    'ts': l.timestamp
                } for l in logs]
                if len(logs)> 25:
                    logs = logs[-25:]

                msg_dict = {
                    'datapoints': data_points,
                    'alarms': alarms,
                    'alarm_records': alarm_records,
                    'logs': logs,
                    'status': alarm_system.system_status
                }

                await websocket.send_json(msg_dict)
                await asyncio.sleep(2)
    except Exception as e:
        print(e)

@app.post("/traffic_record")
async def traffic_record(carril_izq: int, carril_der: int):
    with Session() as db: 
        traffic_record = TrafficRecord(
            carril_izq=carril_izq, 
            carril_der=carril_der, 
            timestamp=datetime.now().strftime(pattern)
        )
        
        msg = Log(
            description= f"Registro de tráfico añadido: {traffic_record.carril_izq}|{traffic_record.carril_der} (izq|der)",
            timestamp= datetime.now().strftime(pattern)
        )

        db.add(traffic_record)
        db.commit()

        db.add(msg)
        db.commit()
    return {"message": "TrafficRecord created successfully"}

@app.post("/day-traffic-csv")
async def day_traffic_csv(data: DayData):
    print(data.day_str)
    with Session() as db:
        data_points = db.query(TrafficRecord).all()
        data_points = [{
                'ts': dp.timestamp,
                'carril_izq': dp.carril_izq,
                'carril_der': dp.carril_der,
            } for dp in data_points]
        
        df = pd.DataFrame(data_points)

        day_df = df.loc[df['ts'].str.contains(data.day_str)]# .to_csv(index=False)
        print(day_df.shape)
        if day_df.shape[0] != 0:
            day_csv = day_df.to_csv(index=False)

            buffer = StringIO()
            buffer.write(day_csv)
            buffer.seek(0)

            response = Response(
                content=buffer.getvalue(),
                media_type='text/csv'
            )

            response.headers["Content-Disposition"] = "attachment; filename=mydata.csv"
            
            return response
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail= "Day not found",
            )


@app.post("/day-alarm-csv")
async def day_alarm_csv(data: DayData):
    print(data.day_str)
    with Session() as db:
        alarm_history = db.query(Alarm_Event).all()
        alarm_history = [{
                'ts': al.timestamp,
                'identifier': al.alarm_identifier,
                'priority': al.priority,
            } for al in alarm_history]
        
        df = pd.DataFrame(alarm_history)

        day_df = df.loc[df['ts'].str.contains(data.day_str)] # .to_csv(index=False)
        print(day_df.shape)
        
        if day_df.shape[0] != 0:
            day_csv = day_df.to_csv(index=False)

            buffer = StringIO()
            buffer.write(day_csv)
            buffer.seek(0)

            response = Response(
                content=buffer.getvalue(),
                media_type='text/csv'
            )

            response.headers["Content-Disposition"] = "attachment; filename=mydata.csv"
            
            return response
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail= "Day not found",
            )

@app.get("/traffic-csv")
async def traffic_csv():
    with Session() as db:
        data_points = db.query(TrafficRecord).all()
        data_points = [{
                'ts': dp.timestamp,
                'carril_izq': dp.carril_izq,
                'carril_der': dp.carril_der,
            } for dp in data_points]
        
        csv_file = pd.DataFrame(data_points).to_csv(index=False)

        buffer = StringIO()
        buffer.write(csv_file)
        buffer.seek(0)

        response = Response(
            content=buffer.getvalue(),
            media_type='text/csv'
        )

        response.headers["Content-Disposition"] = "attachment; filename=mydata.csv"
        
        return response


@app.get("/alarm-csv")
async def alarms_csv():
    with Session() as db:
        alarms = db.query(Alarm_Event).all()
        alarms = [{
                'ts': al.timestamp,
                'identifier': al.alarm_identifier,
                'priority': al.priority,
            } for al in alarms]
        
        csv_file = pd.DataFrame(alarms).to_csv(index=False)

        buffer = StringIO()
        buffer.write(csv_file)
        buffer.seek(0)

        response = Response(
            content=buffer.getvalue(),
            media_type='text/csv'
        )

        response.headers["Content-Disposition"] = "attachment; filename=alarms.csv"
        
        return response

@app.post("/alarm-action")
async def alarm_action(data: AlarmData):

    if data.identifier.startswith('COM'):
        alarm_system.deactivate_alarm(
            alarm_identifier= data.identifier,
            alarm_type= 'communication'
        )
    else:
        alarm_system.deactivate_alarm(
            alarm_identifier= data.identifier,
            alarm_type= 'traffic'
        )


    with Session() as db:
        msg= Log(
            description= f"{data.identifier}: {data.action}",
            timestamp= datetime.now().strftime(pattern)
        )
        db.add(msg)
        db.commit()

    return {"message": "action received successfully"}

@app.get('/', response_class=HTMLResponse)
async def homepage(request: Request):

    context = {
        'site': 'STLight',
        'logo': 'static/images/logo.jpeg',
        'title': 'Inicio',
        'request': request,
        'image_path': '/static/images/process.png',
    }

    return templates.TemplateResponse('home.html', context=context)


@app.get('/alarms', response_class=HTMLResponse)
async def alarm_page(request: Request):

    context = {
        'site': 'STLight',
        'logo': 'static/images/logo.jpeg',
        'title': 'Alarmas',
        'request': request,
    }

    return templates.TemplateResponse('alarma.html', context=context)

@app.get('/traffic-history', response_class=HTMLResponse)
async def traffic_history_page(request: Request):

    context = {
        'site': 'STLight',
        'logo': 'static/images/logo.jpeg',
        'title': 'Históricos',
        'request': request,
    }

    return templates.TemplateResponse('traffic-history.html', context=context)

@app.get('/alarm-history', response_class=HTMLResponse)
async def alarm_history_page(request: Request):

    context = {
        'site': 'STLight',
        'logo': 'static/images/logo.jpeg',
        'title': 'Históricos',
        'request': request,
    }

    return templates.TemplateResponse('alarm-history.html', context=context)

@app.get('/logs', response_class=HTMLResponse)
async def logs_page(request: Request):

    context = {
        'site': 'STLight',
        'logo': 'static/images/logo.jpeg',
        'title': 'Notificaciones',
        'request': request,
    }

    return templates.TemplateResponse('logs.html', context=context)