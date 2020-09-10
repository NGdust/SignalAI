import json
import os
import uuid

import redis

from flask import Flask, render_template, request, make_response, jsonify, url_for
from flask_migrate import Migrate, MigrateCommand
from flask_script import Manager
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename, redirect

from config import Configuration
from modules.amqp import loop, send
from modules.filebase import WassabiStorageTransport, FirebaseStorageTransport

app = Flask(__name__, static_folder="static")
app.config.from_object(Configuration)

# выводить в консоль только ошибки
import logging

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

db = SQLAlchemy(app)


#
# migrate = Migrate(app, db)
# manager = Manager(app)
# manager.add_command('db', MigrateCommand)
#


class SerialQuestion(db.Model):
    __tablename__ = 'question'

    id = db.Column(db.Integer, primary_key=True)
    group = db.Column(db.String)
    category = db.Column(db.String)
    order = db.Column(db.Integer)
    question = db.Column(db.Text, nullable=False, default='')
    bad = db.Column(db.Boolean)
    netral = db.Column(db.Boolean)
    good = db.Column(db.Boolean)
    fix = db.Column(db.Boolean)

    def __repr__(self):
        return '{}'.format(self.question)


class TreeQuestion(db.Model):
    __tablename__ = 'tree_question'

    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String)
    parent_id = db.Column(db.Integer)
    question = db.Column(db.Text, nullable=False, default='')
    emotion = db.Column(db.String)
    intensiveStart = db.Column(db.Integer)
    intensiveEnd = db.Column(db.Integer)
    boolean = db.Column(db.String)
    checkEmotion = db.Column(db.Boolean)
    checkIntensive = db.Column(db.Boolean)
    checkBoolean = db.Column(db.Boolean)
    tip = db.Column(db.String)

    def __repr__(self):
        return '{}'.format(self.question)


class Answer(db.Model):
    __tablename__ = 'answer'

    id = db.Column(db.Integer, primary_key=True)
    index = db.Column(db.String)
    answer = db.Column(db.String)

    def __repr__(self):
        return '{}'.format(self.answer)


class User(db.Model):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    csrftoken = db.Column(db.String)
    categoryQuestion = db.Column(db.String)
    groupQuestion = db.Column(db.String, default='PB')
    orderQuestion = db.Column(db.Integer, default=1)
    resPB = db.Column(db.Integer, default=0)
    resTF = db.Column(db.Integer, default=0)
    resB = db.Column(db.Integer, default=0)
    lastEmotion = db.Column(db.String)
    maxEmotionsList = db.Column(db.String, default='')
    outEmotionList = db.Column(db.Boolean, default=True)

    def __init__(self, csrftoken):
        self.csrftoken = csrftoken


db.create_all()


def resetUser(user):
    user.groupQuestion = 'PB'
    user.orderQuestion = 1
    user.categoryQuestion = ''
    user.resPB = 0
    user.resTF = 0
    user.resB = 0
    user.maxEmotionsList = ''
    user.lastEmotion = ''
    db.session.commit()


@app.route('/', methods=['GET', 'POST'])
def index():
    csrftoken = request.cookies.get('csrftoken')
    responce = make_response(render_template('main.html'))
    if not csrftoken:
        csrftoken = str(uuid.uuid4().hex[:16])
        responce.set_cookie('csrftoken', csrftoken, max_age=60 * 60 * 60)
    user = User.query.filter_by(csrftoken=csrftoken).first()
    if not user:
        new_user = User(csrftoken=csrftoken)
        db.session.add(new_user)
        db.session.commit()
    else:
        resetUser(user)
    return responce


@app.route('/categories', methods=['GET', 'POST'])
def categories():
    csrftoken = request.cookies.get('csrftoken')
    user = User.query.filter_by(csrftoken=csrftoken).first()
    resetUser(user)
    return render_template('categories.html', user=user)

@app.route('/categories/<type>/<category>', methods=['GET', 'POST'])
def category(type, category):
    body = {'csrftoken': request.cookies.get('csrftoken')}

    # Не даем пользователю зайти, если он еще не прошел главную там происходит регистрацие в БД
    if not User.query.filter_by(csrftoken=request.cookies.get('csrftoken')).first():
        return redirect(url_for('index'))
    user = User.query.filter_by(csrftoken=request.cookies.get('csrftoken')).first()
    user.categoryQuestion = category
    resetUser(user)
    db.session.commit()

    orderQuestion = user.orderQuestion
    groupQuestion = user.groupQuestion
    if type == 'serial':
        question = SerialQuestion.query.filter_by(category=category, group=groupQuestion, order=orderQuestion).first()
        textQuestion = question.question
    else:
        question = TreeQuestion.query.filter_by(category=category, id=orderQuestion).first()
        textQuestion = question.question.replace('[emotion]', user.maxEmotionsList)

    if request.method == 'POST':
        # из за каких либо ошибок может копиться кэш, поэтому удаляем от прошлых ответов
        getRedisMessage(key=body['csrftoken'])
        if type == 'serial':
            sendMessageInRabbit(request, body)
        else:
            # Проверяем на что нужно проверять вопрос и сохраняем в редис
            if question.checkEmotion:
                sendMessageInRabbit(request, body)
            elif question.checkIntensive:
                try:
                    intensive = int(request.form.get('text'))
                    if intensive < 1 or intensive > 10:
                        sendRedisMessage(body['csrftoken'], json.dumps({'errorMessage': 'Error number'}))
                    else:
                        sendRedisMessage(body['csrftoken'], json.dumps({'intensive': request.form.get('text')}))
                except:
                    sendRedisMessage(body['csrftoken'], json.dumps({'errorMessage': 'Not number'}))
            elif question.checkBoolean:
                if request.form.get('text').lower() == 'y':
                    req = 'Y'
                    sendRedisMessage(body['csrftoken'], json.dumps({'boolean': req}))
                elif request.form.get('text').lower() == 'n':
                    req = 'N'
                    sendRedisMessage(body['csrftoken'], json.dumps({'boolean': req}))
                else:
                    sendRedisMessage(body['csrftoken'], json.dumps({'errorMessage': 'Error input (Y/N)'}))

    return render_template('questions.html', textQuestion=textQuestion, tip=question.tip)

@app.route('/updateUser', methods=['POST'])
def updateUserOutEmotion():
    data = request.json
    csrftoken = getCookies(data.pop('cookies'), 'csrftoken')
    db.session.query(User).filter_by(csrftoken=csrftoken).update(data)
    db.session.commit()
    print(' [X] Update user')
    return json.dumps({}), 200


@app.route('/updateQuestion', methods=['POST'])
def newQuestion():
    csrftoken = getCookies(request.form.get('cookies'), 'csrftoken')
    typeQuestion = request.form.get('url').split('/')[-2]

    user = User.query.filter_by(csrftoken=csrftoken).first()

    redisData = getRedisMessage(key=csrftoken)
    if redisData:
        # Сохраняем индекс эмоций за прошлый вопрос
        if 'emotionIndex' in redisData:
            user.lastEmotion = redisData['emotionIndex']
            user.maxEmotionsList = redisData['maxEmotionsList']
            db.session.commit()

        # Передаем пользователю последний вопрос и сообщение об ошибки
        if 'errorMessage' in redisData:
            if typeQuestion == 'serial':
                lastQuestion = SerialQuestion.query.filter_by(category=user.categoryQuestion, group=user.groupQuestion, order=user.orderQuestion).first()
            elif typeQuestion == 'tree':
                lastQuestion = TreeQuestion.query.filter_by(id=user.orderQuestion).first()
            return json.dumps({'errorMessage': redisData['errorMessage'], 'question': lastQuestion.question, 'isInputText': lastQuestion.checkEmotion})

        # Определяем структуру вопросов
        if typeQuestion == 'serial':
            return getNewSerialQuestion(user, redisData)
        elif typeQuestion == 'tree':
            return getNewTreeQuestion(user, redisData)

    return make_response("false")


"""
Функция отправкии сообщений в очередь
"""


def sendMessageInRabbit(request, body):
    print(' [x] Send message to SDK')
    if 'file' in request.files:
        # Сохраняем файл
        file = request.files['file']
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(file.filename))
        file.save(file_path)

        # Загружаем на firebase и удаляем из временной папки
        url = FirebaseStorageTransport(from_filename=file_path).upload()
        os.remove(file_path)

        body['file'] = url
    elif request.form.get('text') != '':
        text = request.form.get('text')
        body['text'] = text

    loop.run_until_complete(send(body, 'emoshape'))


"""
Вспомогательные функции
"""


def updateUser(user, order, group='PB', indexEmotion=0):
    user.orderQuestion = order
    user.groupQuestion = group
    if group == 'PB':
        user.resPB += int(indexEmotion)
    elif group == 'TF':
        user.resTF += int(indexEmotion)
    elif group == 'B':
        user.resB += int(indexEmotion)
    db.session.commit()


def getCookies(cookies, field):
    for i in cookies.split('; '):
        if field in i:
            search_field = i.split('=')[1]
            return search_field


def getRedisMessage(key=''):
    if 'DEBUG' in os.environ:
        r = redis.Redis(host='redis')
    else:
        r = redis.Redis()

    for item in r.scan_iter():
        if key in str(item):
            redisData = r.get(key)
            r.delete(key)
            return json.loads(redisData)
    return False


def sendRedisMessage(key, message):
    if 'DEBUG' in os.environ:
        r = redis.Redis(host='redis')
    else:
        r = redis.Redis()
    r.set(key, message)


"""
Функции нахождения вопросов в базе данных
"""



def checkResultEmotionForAnswer(user):
    """
    Состовление конечного отчета по завершению опроса
    в базе данных в таблице с ответами должны лежать шаблоны с ключевыми словами
    - PB_EMOTIONS
    - TF_EMOTIONS
    - B_EMOTIONS
    - GENERAL_EMOTIONS
    """

    x = '1' if user.resPB >= 0 else '-1'
    y = '1' if user.resTF >= 0 else '-1'
    z = '1' if user.resB >= 0 else '-1'

    res = user.resPB + user.resTF + user.resB

    textPositive = 'Positive emotions'
    textNegative = 'Negative emotions'

    resultEmotion = x + y + z
    resultAnswer = Answer.query.filter_by(index=resultEmotion).first().answer
    resultAnswer = resultAnswer.replace('PB_EMOTIONS', textPositive if user.resPB >= 0 else textNegative)
    resultAnswer = resultAnswer.replace('TF_EMOTIONS', textPositive if user.resTF >= 0 else textNegative)
    resultAnswer = resultAnswer.replace('B_EMOTIONS', textPositive if user.resB >= 0 else textNegative)
    resultAnswer = resultAnswer.replace('GENERAL_EMOTIONS', textPositive if res >= 0 else textNegative)
    return resultAnswer


def nextSerialQuestion(userCategory, userOrder, group, indexEmotion):
    resultQuestion = ''
    q = SerialQuestion.query.filter_by(category=userCategory, group=group).all()

    for quest in range(userOrder, len(q)):
        childQuestion = SerialQuestion.query.filter_by(category=userCategory, group=group, order=quest + 1).first()
        if childQuestion.fix:
            resultQuestion = childQuestion
            break
        elif childQuestion.bad and (int(indexEmotion) == -1):
            resultQuestion = childQuestion
            break
        elif childQuestion.netral and (int(indexEmotion) == 0):
            resultQuestion = childQuestion
            break
        elif childQuestion.good and (int(indexEmotion) == 1):
            resultQuestion = childQuestion
            break
    return resultQuestion


def getNewSerialQuestion(user, redisData):
    indexEmotion = redisData['emotionIndex']

    resultQuestion = nextSerialQuestion(user.categoryQuestion, user.orderQuestion, user.groupQuestion, indexEmotion)
    responseData = {'maxEmotions': redisData['maxEmotions'], 'symblTopics': redisData['symblTopics']}
    # сохраняем результаты эмоций пользователя
    updateUser(user, user.orderQuestion, user.groupQuestion, indexEmotion=indexEmotion)

    # Если вопрос не найден, блок вопросов закончен
    if not resultQuestion:
        # Переходы на новый блок вопросов
        if user.groupQuestion == 'PB':
            group = 'TF'
            stepid = 0
            resultQuestion = nextSerialQuestion(user.categoryQuestion, stepid, group, indexEmotion)
            responseData["question"] = resultQuestion.question

            # Фиксируем положение пользователя на вопросе
            updateUser(user, resultQuestion.order, resultQuestion.group)
            return json.dumps(responseData)

        elif user.groupQuestion == 'TF':
            group = 'B'
            stepid = 0
            resultQuestion = nextSerialQuestion(user.categoryQuestion, stepid, group, indexEmotion)
            responseData["question"] = resultQuestion.question

            # Фиксируем положение пользователя на вопросе
            updateUser(user, resultQuestion.order, resultQuestion.group)
            return json.dumps(responseData)

        # Проверка на конец блоков вопросов
        elif user.groupQuestion == 'B':
            resultAnswer = checkResultEmotionForAnswer(user)
            return json.dumps({"answerCategory": resultAnswer})

    updateUser(user, resultQuestion.order, resultQuestion.group)
    responseData["question"] = resultQuestion.question
    return json.dumps(responseData)


def getQ(user, question):
    textQuestion = question.question.replace('[emotion]', user.maxEmotionsList)
    responseData = {'question': textQuestion, 'tipMessage': question.tip, 'isInputText': question.checkEmotion}
    user.orderQuestion = question.id
    db.session.commit()

    # Если вопросу не надо что-то проверять выводим как конечный ответ
    if not question.checkEmotion and not question.checkIntensive and not question.checkBoolean:
        textQuestion = question.question.replace('[emotion]', user.maxEmotionsList)
        return {"answerCategory": textQuestion}
    return responseData

def getNewTreeQuestion(user, redisData):
    lastQuestion = TreeQuestion.query.filter_by(category=user.categoryQuestion, id=user.orderQuestion).first()
    childQuestion = TreeQuestion.query.filter_by(category=user.categoryQuestion, parent_id=lastQuestion.id).all()
    responceData = {}
    if ('maxEmotions' in redisData) and user.outEmotionList:
        responceData['maxEmotions'] = redisData['maxEmotions']

    # Если есть только один дочерний вопрос
    if len(childQuestion) == 1:
        responceData.update(getQ(user, childQuestion[0]))
        return json.dumps(responceData)

    for question in childQuestion:

        # Если вопрос ожидает эмоции и интервал, это второй уровень вопросов
        if question.emotion and question.intensiveStart:
            intensive = int(redisData['intensive'])
            if (user.lastEmotion in question.emotion) and (
                    intensive >= question.intensiveStart and intensive <= question.intensiveEnd):
                responceData.update(getQ(user, question))
                return json.dumps(responceData)
        else:
            if question.emotion:
                if str(redisData['emotionIndex']) in question.emotion:
                    responceData.update(getQ(user, question))
                    return json.dumps(responceData)
            elif question.intensiveStart:
                intensive = int(redisData['intensive'])
                if intensive > question.intensiveStart and intensive < question.intensiveEnd:
                    responceData.update(getQ(user, question))
                    return json.dumps(responceData)
            elif question.boolean:
                if redisData['boolean'] in question.boolean:
                    responceData.update(getQ(user, question))
                    return json.dumps(responceData)
