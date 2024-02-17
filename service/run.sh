export FLASK_APP=app.py
export FLASK_DEBUG=true
export OPENAI_MODEL="gpt-4-1106-preview"

# Read .env.sh
if [ -f .env.sh ]; then
    source .env.sh
fi


alembic upgrade head
flask run --host=0.0.0.0 --port=4000
