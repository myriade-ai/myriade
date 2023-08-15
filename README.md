# Ada

ChatGPT for data analysis.

Branch your database, and simply ask.

<img width="1510" alt="CleanShot 2023-06-24 at 14 02 46@2x" src="https://github.com/BenderV/ada/assets/2799516/56f0a411-0ae5-4003-aebc-0c1b83d56a54">

## Pre-requesite

- Create Postgres database

## Install

in /service

- `poetry install` -- install dependencies
- `export OPENAI_API_KEY=XXX` -- set your OpenAI API key
- `export DATABASE_URL=XXX` -- set your Postgres database URL
- `flask run` -- run the backend

in /view

- `yarn` -- install dependencies
- `yarn dev` -- run the front

Go on `http://localhost:5173`

## Tech stack

- AI based on OpenAI's GPT-4 API
- Frontend: Vue3, Vite
- Backend: Python
- Database: Postgres
