import logging
from openai import OpenAI, OpenAIError
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ConversationHandler,
    ContextTypes,
)

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Set your OpenAI API key
openai_api_key = "sk-proj-dCUI5hnYzoSoJ6jfwYtxT3BlbkFJ7nRGqCYHpU7jTQHMoLY7"
client = OpenAI(api_key=openai_api_key)

# Define the states for the conversation
ANSWERING_QUESTIONS = range(7)

# Define the questions
questions = [
    "Quel est votre nom et prénom ?",
    "Pouvez-vous me parler un peu de vous ?",
]

answers = {}

# Define the command handler for starting the conversation
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    if user_id not in answers:
        answers[user_id] = []

    welcome_message = (
        "Bonjour et bienvenue sur Chatbot Ronald ! 🎓\n\n"
        "Pour commencer, veuillez me donner votre nom et prénom :"
    )
    await update.message.reply_text(welcome_message)
    return ANSWERING_QUESTIONS

async def ask_questions(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    question_number = len(answers[user_id])

    if question_number < len(questions):
        if question_number == 0:
            await update.message.reply_text(questions[question_number])
        else:
            personalized_question = questions[question_number]
            await update.message.reply_text(personalized_question)

        return ANSWERING_QUESTIONS
    else:
        return await generate_motivational_letter(update, context)

async def receive_answers(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    answers[user_id].append(update.message.text)
    return await ask_questions(update, context)

async def generate_motivational_letter(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id

    # Construct the prompt
    prompt = "Écrire une lettre de motivation en français destinée au bureau des admissions d'une université, basée sur les informations suivantes. Assurez-vous d'inclure mon nom à la fin de la lettre :\n\n"
    for i, question in enumerate(questions):
        prompt += f"{questions[i]}\nAnswer: {answers[user_id][i]}\n\n"

    messages = [
        {"role": "system", "content": "Vous êtes un assistant utile, compétent en rédaction de lettres de motivation."},
        {"role": "user", "content": prompt}
    ]

    try:
        # Use ChatGPT API to generate the rest of the letter
        completion = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=1500,
            temperature=0.7
        )

        letter = completion.choices[0].message.content.strip()
        await update.message.reply_text("Merci pour vos réponses. Voici votre lettre de motivation :\n\n" + letter)

    except OpenAIError as e:
        await update.message.reply_text(f"Une erreur s'est produite lors de la génération de la lettre : {e}")

    # Clear user's answers
    del answers[user_id]
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    if user_id in answers:
        del answers[user_id]
    await update.message.reply_text('Conversation annulée.')
    return ConversationHandler.END

def main():
    # Set up the Telegram bot
    application = ApplicationBuilder().token("7369215374:AAGh4lEKFkXfpOxlND6cGPNIpLPBTZK6F7M").build()

    # Define the conversation handler
    conversation_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            ANSWERING_QUESTIONS: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_answers)]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    application.add_handler(conversation_handler)

    # Start the bot
    application.run_polling()

if __name__ == '__main__':
    main()
