# Ada: ChatGPT for Business Intelligence

**Branch your database and interact with it in natural language.**

![Ada Demo Screenshot](https://github.com/BenderV/ada/assets/2799516/56f0a411-0ae5-4003-aebc-0c1b83d56a54)

## Features

- **Natural Language Queries**: Easily pull insights without writing complex queries.
- **Integration with Postgres**: Connect Ada with your existing Postgres database.
- **Powered by OpenAI's GPT-4**: Experience cutting-edge AI-driven interactions.

## Pre-requisites

1. PostgreSQL installed and running.
2. OpenAI API key. If you don't have one, get it [here](https://www.openai.com/).

ℹ️ Note: while you can use GPT-3, we don't recommend trying it out with Ada.
If you don't have access to GPT-4, you can contact me on [Twitter](https://twitter.com/benderville) for a beta invite of Ada.

## Installation

### Backend Setup (in `/service` directory)

1. **Setup Virtual Environment** (Optional but recommended):

   ```bash
   poetry shell
   ```

2. **Install Dependencies**:

   ```bash
   poetry install
   ```

3. **Set Environment Variables**:

   ```bash
   export OPENAI_API_KEY=<Your_OpenAI_API_Key>
   export DATABASE_URL=<Your_Postgres_Database_URL>
   ```

4. **Run the Backend**:
   ```bash
   flask run
   ```

### Frontend Setup (in `/view` directory)

1. **Install Dependencies**:

   ```bash
   yarn
   ```

2. **Run the Frontend**:
   ```bash
   yarn dev
   ```

After completing the steps, open your browser and visit: [http://localhost:5173](http://localhost:5173)

## Tech Stack

- **AI Interaction**: Powered by OpenAI's GPT-4 API.
- **Frontend**: Built using Vue3 and Vite.
- **Backend**: Developed in Python.
- **Database**: Postgres.

## Contribution

If you want to contribute, you can ping me on [Twitter](https://twitter.com/benderville).

## License

[MIT](LICENSE.md) - Feel free to use and modify, but please attribute appropriately.
