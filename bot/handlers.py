from telegram import Update
from telegram.ext import CommandHandler, MessageHandler, filters
import json
import httpx
from openai import OpenAI
from config import TOKEN, OPENAI_API_KEY
from sentence_transformers import SentenceTransformer, util



# Создаем клиент OpenAI
proxy_url = "http://189.240.60.171:9090"  # Используем ваш рабочий прокси
client = OpenAI(
    api_key=OPENAI_API_KEY,
    http_client=httpx.Client(proxy=proxy_url))  # Используем параметр proxy



assistant = client.beta.assistants.create(
    name="LATOKEN Assistant",
    instructions="Вы помогающий ассистент, который отвечает на вопросы о LATOKEN, хакатоне и Culture Deck.",
    model="gpt-4",
    tools=[]  # Пустой список, если функции не нужны
)

# Получение ID ассистента
ASSISTANT_ID = assistant.id

# Функция для взаимодействия с ассистентом
def ask_assistant(user_input):
    response = client.beta.assistants.create_and_run(
        assistant_id=ASSISTANT_ID,
        thread={
            "messages": [
                {"role": "user", "content": user_input}
            ]
        }
    )
    return response.choices[0].message.content

# Загрузка модели для векторного поиска
model = SentenceTransformer('all-MiniLM-L6-v2')

# Загрузка данных из JSON
def load_json_data():
    with open('Dataset/01.json', 'r', encoding='utf-8') as f:
        data_01 = json.load(f)

    with open('Dataset/02.json', 'r', encoding='utf-8') as f:
        data_02 = json.load(f)

    return data_01, data_02

# Загрузка Culture Deck
def load_culture_deck():
    with open('culture_2.txt', 'r', encoding='utf-8') as f:
        content = f.read()
    # Разделяем текст на фрагменты (например, по абзацам)
    fragments = content.split('\n\n')  # Предполагаем, что абзацы разделены двумя переносами строки
    return fragments

# Поиск релевантных фрагментов
def find_relevant_fragments(query, fragments, top_k=3):
    # Кодируем запрос и фрагменты
    query_embedding = model.encode(query, convert_to_tensor=True)
    fragment_embeddings = model.encode(fragments, convert_to_tensor=True)

    # Вычисляем схожесть
    cos_scores = util.cos_sim(query_embedding, fragment_embeddings)[0]

    # Сортируем по убыванию схожести
    top_results = sorted(zip(fragments, cos_scores), key=lambda x: x[1], reverse=True)[:top_k]

    return [result[0] for result in top_results]

# Формирование промта
def generate_prompt(user_input, data_01, data_02, culture_context):
    prompt = f"""
    Информация о компании LATOKEN:
    - Миссия: {data_01['mission']}
    - Цели: {', '.join(data_01['goals'])}
    - Ценности: {', '.join(data_01['values'])}
    - Культура: {data_01['culture']}
    - Карьера: {data_01['careers']}

    Информация о хакатоне LATOKEN:
    - Описание: {data_02['description']}
    - Цели: {', '.join(data_02['objectives'])}
    - Условия участия: {data_02['participation']['eligibility']}
    - Призы: {data_02['prizes']}
    - Контакты: {data_02['contact']['email']}, {data_02['contact']['website']}

    Контекст из Culture Deck:
    {culture_context}

    Вопрос пользователя: {user_input}
    """
    return prompt

# Запрос к GPT-4
def ask_gpt4(prompt):
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "Вы помогающий ассистент."},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content



# Список вопросов для тестирования
TEST_QUESTIONS = [

    "Почему Латокен помогает людям изучать и покупать активы?",
    "Зачем нужен Sugar Cookie тест?",
    "Зачем нужен Wartime СЕО?",
    "В каких случаях стресс полезен и в каких вреден?"
]

# Обработка команды /start
async def start(update: Update, context) -> None:
    await update.message.reply_text('Привет! Я ваш Telegram-бот. Чем могу помочь?')

async def help_command(update: Update, context) -> None:
    await update.message.reply_text(
        'Я могу ответить на ваши вопросы о LATOKEN и хакатоне. Просто напишите мне что-нибудь.')

# Обработка текстовых сообщений
async def handle_message(update: Update, context) -> None:
    user_input = update.message.text

    # Загружаем данные из JSON
    data_01, data_02 = load_json_data()

    # Загружаем Culture Deck
    culture_fragments = load_culture_deck()

    # Ищем релевантные фрагменты из Culture Deck
    relevant_fragments = find_relevant_fragments(user_input, culture_fragments)

    # Формируем промт с учетом Culture Deck
    culture_context = "\n".join(relevant_fragments)
    prompt = generate_prompt(user_input, data_01, data_02, culture_context)

    # Запрашиваем ответ у GPT-4
    response = ask_gpt4(prompt)

    # Отправляем ответ пользователю
    await update.message.reply_text(response)

    # Задаем вопрос из теста
    if TEST_QUESTIONS:
        test_question = TEST_QUESTIONS.pop(0)
        await update.message.reply_text(f"Теперь вопрос для вас: {test_question}")
    if not TEST_QUESTIONS:
        await update.message.reply_text("Вы ответили на все вопросы. Спасибо за участие!")

def evaluate_user_answer(user_answer, correct_answer):
    if user_answer.lower() == correct_answer.lower():
        return "Верно! Вы хорошо разбираетесь в теме."
    else:
        return f"Почти правильно, но давайте уточним: {correct_answer}"

# Регистрация обработчиков
def register_handlers(application):
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('help', help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))