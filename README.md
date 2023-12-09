# ADA: Accelerate Data Analysis, with AI
Ada is the latest AI tool to explore your data in a safe, fast & accessible way.

![Ada Demo Screenshot](https://github.com/BenderV/ada/assets/2799516/6b1e457c-477d-4b22-a471-915c5f8ac8b6)

## Features
* **Easy set up:** Run Ada locally in 5 minutes
* **Human Friendly:** Query in English, Ada will take care of the rest.
* **“Take Over” Mode:** Built-in Editor to run SQL
* **Built-in Privacy & Safety:** Use with a peace of mind

## Demo
Check out this [2 min demo video](https://www.youtube.com/watch?v=rh8CWB0ClOc) to see Ada in action.

## Quick Start Guide
### Pre-requisites
ℹ️ Note: get an OpenAI API key. If you don't have one, get it [here](https://www.openai.com/).

### Docker installation
```
docker-compose up -d
```

### Manual installation
#### Backend Setup (in `/service` directory)

1. **Install Dependencies**:
   ```bash
   poetry install
   ```

2. **Set Environment Variables**:
   in `service/.env.sh` file:

   ```bash
   export OPENAI_API_KEY=<Your_OpenAI_API_Key>
   export DATABASE_URL=<Your_Postgres_Database_URL>
   ```

3. **Run the Backend**:
   ```bash
   bash run.sh
   ```

### Frontend Setup (in `/view` directory)
Install Dependencies
```
yarn
```

Run the front-end
```
yarn dev
```

After completing the steps, open your browser and visit: [http://localhost:5173](http://localhost:5173)

## Privacy & Safety
We have developed built-in features to protect privacy and insure safety
* **Preview only:** Model only have preview of the requested data
* **“Privacy protection”:** hide fields about name, location
* **“Safe mode”:** limit to read-only query

## Tech Stacks
- ****AI Interaction****: Using Autochat library with OpenAI GPT-4 API.
- ****Frontend****: Built using Vue3 and Vite
- ****Backend****: Developed in Python
- ****Database****: Postgres

## FAQs
Q: How secure is my data with Ada / OpenAI?
A: Since it's open source, you can run Ada on your own server and keep your data private. OpenAI's API is also secure and encrypted, and they don't use your data for training with the API.

## Troubleshooting & Contribution
For any issues, please open an issue on GitHub or contact me on [Twitter](https://twitter.com/benderville).

## License
[MIT](LICENSE.md) - Feel free to use and modify, but please attribute appropriately.

